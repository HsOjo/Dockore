import asyncio
import json
import os
import shlex
import threading
from typing import Optional

from docker.errors import NotFound
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_docker
from app.api.deps import StackContext, get_stack_ctx
from app.core import config
from app.core.broadcast import manager
from app.core.security import verify_terminal_ticket, verify_token
from app.services.compose import stack_tasks
from app.services.docker.client import Docker

router = APIRouter()


async def _ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if not token or not verify_token(token, config.settings.dockore_token):
        await websocket.close(code=1008)
        return False
    return True


def _sock_recv(sock, n: int) -> bytes:
    if hasattr(sock, "recv"):
        return sock.recv(n)
    return sock.read(n)


def _sock_send(sock, data: bytes) -> None:
    # docker-py may return a raw socket (send/recv) or a read-only SocketIO
    # whose underlying writable socket lives on the `_sock` attribute.
    raw = getattr(sock, "_sock", None)
    if raw is not None and hasattr(raw, "send"):
        raw.send(data)
    elif hasattr(sock, "send"):
        sock.send(data)
    else:
        sock.write(data)


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
        stream = await docker.container.open_log_stream(id, since, until, follow)
    except NotFound:
        await websocket.close(code=1008, reason="Container not found")
        return

    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _stream():
        try:
            for chunk in stream:
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, e)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=_stream, daemon=True).start()
    try:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            if isinstance(chunk, Exception):
                await websocket.close(code=1011, reason=str(chunk))
                return
            await websocket.send_text(chunk.decode(errors="ignore"))
        await websocket.close()
    except (WebSocketDisconnect, RuntimeError):
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
    except NotFound:
        await websocket.close(code=1008, reason="Container not found")
        return
    if status != "running":
        await websocket.close(code=1008, reason="Container not running")
        return

    command: Optional[str] = payload.get("command")
    cmd = shlex.split(command) if command else ["/bin/sh"]
    try:
        exec_id = await docker.container.exec_create_tty(container_id, cmd)
    except Exception as e:
        await websocket.close(code=1011, reason=f"exec_create failed: {e}")
        return

    sock = await docker.container.exec_start_socket(exec_id)
    await websocket.accept()

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    stop = threading.Event()

    def _reader():
        try:
            while not stop.is_set():
                data = _sock_recv(sock, 4096)
                if not data:
                    break
                loop.call_soon_threadsafe(queue.put_nowait, data)
        except Exception:
            pass
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=_reader, daemon=True).start()

    async def _resize(rows: int, cols: int):
        try:
            await docker.container.exec_resize(exec_id, rows, cols)
        except Exception:
            pass

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
                # exec TTY; anything else is terminal input.
                try:
                    ctrl = json.loads(text)
                except json.JSONDecodeError:
                    ctrl = None
                if isinstance(ctrl, dict) and "rows" in ctrl and "cols" in ctrl:
                    await _resize(int(ctrl["rows"]), int(ctrl["cols"]))
                    continue
                data = text.encode()
            if data:
                await asyncio.to_thread(_sock_send, sock, data)

    sender = asyncio.create_task(_sender())
    receiver = asyncio.create_task(_receiver())
    try:
        done, pending = await asyncio.wait(
            {sender, receiver}, return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        stop.set()
        try:
            sock.close()
        except Exception:
            pass
        try:
            await websocket.close()
        except RuntimeError:
            pass
