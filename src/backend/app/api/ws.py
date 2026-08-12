import asyncio
import json
import os
import shlex
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_docker
from app.api.deps import StackContext, get_stack_ctx
from app.core import config
from app.core.broadcast import manager
from app.core.security import verify_terminal_ticket, verify_token
from app.services.cli import CliExecutor, Docker, DockerNotFound
from app.services.compose import stack_tasks

router = APIRouter()


async def _ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if not token or not verify_token(token, config.settings.dockore_token):
        await websocket.close(code=1008)
        return False
    return True


@router.websocket("/ws")
async def events_ws(websocket: WebSocket):
    if not await _ws_auth(websocket):
        return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")
                if msg_type == "stack.resize":
                    await _handle_stack_resize(msg)
                await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def _handle_stack_resize(msg: dict) -> None:
    task_id = msg.get("task_id")
    rows = msg.get("rows")
    cols = msg.get("cols")
    if not task_id or rows is None or cols is None:
        return
    stack_tasks.resize(task_id, int(rows), int(cols))


@router.websocket("/ws/containers/{id}/logs")
async def container_logs_ws(
    websocket: WebSocket, id: str, docker: Docker = Depends(get_docker),
):
    if not await _ws_auth(websocket):
        return

    since = websocket.query_params.get("since")
    until = websocket.query_params.get("until")
    follow = websocket.query_params.get("follow", "").lower() in ("1", "true", "yes")

    try:
        await docker.container.get_status(id)
    except DockerNotFound:
        await websocket.close(code=1008, reason="Container not found")
        return

    args = ["docker", "logs"]
    if since:
        args += ["--since", since]
    if until:
        args += ["--until", until]
    if follow:
        args.append("-f")
    args.append(id)

    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_data(task, data: bytes):
        await queue.put(data.decode(errors="ignore"))

    async def on_done(task):
        await queue.put(None)

    executor = docker.cli.executor
    task = await executor.stream(
        "container.logs", id, args, on_data, on_done=on_done, line_mode=True,
    )

    async def _sender():
        while True:
            data = await queue.get()
            if data is None:
                return
            await websocket.send_text(data)

    async def _receiver():
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                return

    sender = asyncio.create_task(_sender())
    receiver = asyncio.create_task(_receiver())
    try:
        done, pending = await asyncio.wait(
            {sender, receiver}, return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        if sender in done and task.status == "error" and task.error:
            await websocket.close(code=1011, reason=task.error)
            return
    finally:
        await executor.cancel(task.id)
        try:
            await websocket.close()
        except (RuntimeError, WebSocketDisconnect):
            pass


@router.websocket("/ws/stacks/{name}/logs")
async def stack_logs_ws(
    websocket: WebSocket, name: str, ctx: StackContext = Depends(get_stack_ctx),
):
    if not await _ws_auth(websocket):
        return

    follow = websocket.query_params.get("follow", "").lower() in ("1", "true", "yes")

    if not ctx.compose:
        await websocket.close(code=1008, reason="compose CLI not available")
        return

    from app.core import stack_registry

    registrations = await stack_registry.list_all(ctx.session)
    stack = await ctx.stack.get(name, registrations)
    if not stack:
        await websocket.close(code=1008, reason="stack not found")
        return

    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_data(task, data: bytes):
        await queue.put(data)

    async def on_done(task):
        # Sentinel: lets the sender drain queued output before finishing.
        await queue.put(None)

    # Prefer compose file labels / registry data. If the recorded working_dir
    # does not exist on this host (e.g. Docker Desktop paths), fall back to
    # project-name discovery.
    files = stack.get("config_files") or None
    cwd = stack.get("working_dir") or None
    if cwd and not os.path.isdir(cwd):
        files = cwd = None
    if files and not all(os.path.isfile(f) for f in files):
        files = cwd = None

    task = await ctx.compose.logs(
        name,
        on_data,
        files=files,
        cwd=cwd,
        follow=follow,
        on_done=on_done,
    )

    async def _sender():
        while True:
            data = await queue.get()
            if data is None:
                return
            await websocket.send_bytes(data)

    async def _receiver():
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                return

    sender = asyncio.create_task(_sender())
    receiver = asyncio.create_task(_receiver())
    try:
        done, pending = await asyncio.wait(
            {sender, receiver}, return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        if sender in done:
            if task.status == "error" and task.error:
                await websocket.send_text(f"[error] {task.error}\n")
    finally:
        await ctx.compose.executor.cancel(task.id)
        try:
            await websocket.close()
        except (RuntimeError, WebSocketDisconnect):
            pass


@router.websocket("/ws/terminal")
async def terminal_ws(websocket: WebSocket, docker: Docker = Depends(get_docker)):
    ticket = websocket.query_params.get("ticket")
    payload = (
        verify_terminal_ticket(ticket, config.settings.dockore_terminal_expires)
        if ticket else None
    )
    if not payload:
        await websocket.close(code=1008, reason="Invalid or expired ticket")
        return

    container_id = payload["container_id"]
    try:
        status = await docker.container.get_status(container_id)
    except DockerNotFound:
        await websocket.close(code=1008, reason="Container not found")
        return
    if status != "running":
        await websocket.close(code=1008, reason="Container not running")
        return

    command: Optional[str] = payload.get("command")
    cmd = shlex.split(command) if command else ["/bin/sh"]
    args = ["docker", "exec", "-it", container_id, *cmd]

    await _terminal_session(
        websocket, docker.cli.executor, "container.terminal", container_id, args,
    )


@router.websocket("/ws/terminal/host")
async def host_terminal_ws(websocket: WebSocket, docker: Docker = Depends(get_docker)):
    ticket = websocket.query_params.get("ticket")
    payload = (
        verify_terminal_ticket(ticket, config.settings.dockore_terminal_expires)
        if ticket else None
    )
    if not payload or not payload.get("host"):
        await websocket.close(code=1008, reason="Invalid or expired ticket")
        return

    await _terminal_session(websocket, docker.cli.executor, "host.terminal", "-", ["bash", "-l"])


async def _terminal_session(
    websocket: WebSocket,
    executor: CliExecutor,
    kind: str,
    stack: str,
    args: list[str],
):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    async def on_data(task, data: bytes):
        await queue.put(data)

    async def on_done(task):
        await queue.put(None)

    task = await executor.stream(kind, stack, args, on_data, on_done=on_done)

    async def _sender():
        while True:
            data = await queue.get()
            if data is None:
                return
            await websocket.send_bytes(data)

    async def _receiver():
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                return
            text = msg.get("text")
            data = msg.get("bytes")
            if text is not None:
                # JSON control frames ({rows, cols} or {type: resize, ...}) resize the
                # pty; anything else is terminal input.
                try:
                    ctrl = json.loads(text)
                except json.JSONDecodeError:
                    ctrl = None
                if isinstance(ctrl, dict) and "rows" in ctrl and "cols" in ctrl:
                    task.resize(int(ctrl["rows"]), int(ctrl["cols"]))
                    continue
                data = text.encode()
            if data:
                task.write(data)

    sender = asyncio.create_task(_sender())
    receiver = asyncio.create_task(_receiver())
    try:
        done, pending = await asyncio.wait(
            {sender, receiver}, return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        if sender in done and task.status == "error" and task.error:
            await websocket.close(code=1011, reason=task.error)
            return
    finally:
        await executor.cancel(task.id)
        try:
            await websocket.close()
        except (RuntimeError, WebSocketDisconnect):
            pass
