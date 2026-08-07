import asyncio
import json
import shlex
import threading
from typing import Optional

from docker.errors import NotFound
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import resolve_docker
from app.core import config
from app.core.broadcast import manager
from app.core.database import async_session
from app.core.security import verify_terminal_ticket, verify_token
from app.services.docker.container import parse_ts

router = APIRouter()


async def _ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    if not token or not verify_token(token, config.settings.dockore_token):
        await websocket.close(code=1008)
        return False
    return True


async def _resolve_docker():
    async with async_session() as session:
        return await resolve_docker(session)


@router.websocket("/ws")
async def events_ws(websocket: WebSocket):
    if not await _ws_auth(websocket):
        return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                json.loads(data)
                await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@router.websocket("/ws/containers/{id}/logs")
async def container_logs_ws(websocket: WebSocket, id: str):
    if not await _ws_auth(websocket):
        return

    since = websocket.query_params.get("since")
    until = websocket.query_params.get("until")
    follow = websocket.query_params.get("follow", "").lower() in ("1", "true", "yes")

    docker = await _resolve_docker()
    try:
        container = await asyncio.to_thread(docker._client.containers.get, id)
    except NotFound:
        await websocket.close(code=1008, reason="Container not found")
        return

    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _stream():
        try:
            gen = container.logs(
                stream=True, follow=follow,
                since=parse_ts(since), until=parse_ts(until),
            )
            for chunk in gen:
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


@router.websocket("/ws/terminal")
async def terminal_ws(websocket: WebSocket):
    ticket = websocket.query_params.get("ticket")
    payload = (
        verify_terminal_ticket(ticket, config.settings.dockore_terminal_expires)
        if ticket else None
    )
    if not payload:
        await websocket.close(code=1008, reason="Invalid or expired ticket")
        return

    docker = await _resolve_docker()
    try:
        container = await asyncio.to_thread(
            docker._client.containers.get, payload["container_id"],
        )
    except NotFound:
        await websocket.close(code=1008, reason="Container not found")
        return
    if container.status != "running":
        await websocket.close(code=1008, reason="Container not running")
        return

    command: Optional[str] = payload.get("command")
    cmd = shlex.split(command) if command else ["/bin/sh"]
    api = docker.api
    try:
        exec_id = (await asyncio.to_thread(
            api.exec_create, container.id, cmd, tty=True, stdin=True,
        ))["Id"]
    except Exception as e:
        await websocket.close(code=1011, reason=f"exec_create failed: {e}")
        return

    sock = await asyncio.to_thread(api.exec_start, exec_id, socket=True, demux=False)
    await websocket.accept()

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    stop = threading.Event()

    def _reader():
        try:
            while not stop.is_set():
                data = sock.recv(4096)
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
            await asyncio.to_thread(api.exec_resize, exec_id, height=rows, width=cols)
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
                await asyncio.to_thread(sock.send, data)

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
