import json
import time

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.deps import get_docker
from app.core.security import create_terminal_ticket
from app.main import app
from tests.conftest import TOKEN_HASH
from tests.fakes import CONTAINER, FakeDocker

CID = CONTAINER["id"]


@pytest.fixture
def ws_client():
    fake = FakeDocker()
    app.dependency_overrides[get_docker] = lambda: fake
    with TestClient(app) as tc:
        yield tc, fake
    app.dependency_overrides.clear()


def wait_for(cond, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_events_ws_rejects_bad_token(ws_client):
    tc, _ = ws_client
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect("/ws?token=wrong"):
            pass
    assert exc.value.code == 1008


def test_events_ws_rejects_missing_token(ws_client):
    tc, _ = ws_client
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect("/ws"):
            pass
    assert exc.value.code == 1008


def test_events_ws_pong(ws_client):
    tc, _ = ws_client
    with tc.websocket_connect(f"/ws?token={TOKEN_HASH}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        assert ws.receive_json() == {"type": "pong"}
        ws.send_text("not json")


def test_logs_ws_rejects_bad_token(ws_client):
    tc, _ = ws_client
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect(f"/ws/containers/{CID}/logs?token=wrong"):
            pass
    assert exc.value.code == 1008


def test_logs_ws_container_not_found(ws_client):
    tc, _ = ws_client
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect(f"/ws/containers/missing/logs?token={TOKEN_HASH}"):
            pass
    assert exc.value.code == 1008


def test_logs_ws_streams_chunks(ws_client):
    tc, fake = ws_client
    with tc.websocket_connect(
        f"/ws/containers/{CID}/logs?token={TOKEN_HASH}&follow=true"
    ) as ws:
        assert ws.receive_text() == "log line 1\n"
        assert ws.receive_text() == "log line 2\n"
    assert fake.container.log_stream_calls == [
        dict(since=None, until=None, follow=True),
    ]


def test_terminal_ws_rejects_bad_ticket(ws_client):
    tc, _ = ws_client
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect("/ws/terminal?ticket=bad"):
            pass
    assert exc.value.code == 1008


def test_terminal_ws_rejects_missing_container(ws_client):
    tc, _ = ws_client
    ticket = create_terminal_ticket("missing", None)
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect(f"/ws/terminal?ticket={ticket}"):
            pass
    assert exc.value.code == 1008


def test_terminal_ws_full_session(ws_client):
    tc, fake = ws_client
    sock = fake.container.terminal_socket
    ticket = create_terminal_ticket(CID, "/bin/bash")
    with tc.websocket_connect(f"/ws/terminal?ticket={ticket}") as ws:
        sock.feed(b"$ ")
        assert ws.receive_bytes() == b"$ "

        ws.send_text("ls\n")
        assert wait_for(lambda: sock.written == [b"ls\n"])

        ws.send_text(json.dumps({"rows": 24, "cols": 80}))
        assert wait_for(lambda: fake.container.resized == [("exec123", 24, 80)])

        sock.feed(b"file1 file2\n$ ")
        assert ws.receive_bytes() == b"file1 file2\n$ "

        ws.send_bytes(b"\x03")
        assert wait_for(lambda: sock.written[-1] == b"\x03")

        sock.close()
        with pytest.raises(WebSocketDisconnect):
            ws.receive_bytes()

    assert fake.container.exec_created == [(CID, ["/bin/bash"])]


def test_terminal_ws_default_command(ws_client):
    tc, fake = ws_client
    ticket = create_terminal_ticket(CID, None)
    fake.container.terminal_socket.close()
    with tc.websocket_connect(f"/ws/terminal?ticket={ticket}"):
        pass
    assert fake.container.exec_created == [(CID, ["/bin/sh"])]


def test_sock_recv_send_compat():
    import socket as _socket

    from app.api.ws import _sock_recv, _sock_send

    a, b = _socket.socketpair()
    try:
        # 原始 socket：send/recv
        _sock_send(a, b"ping")
        assert _sock_recv(b, 4096) == b"ping"

        # SocketIO 包装：read-only + _sock 可写（docker-py 返回的形态）
        sio = _socket.SocketIO(a, "rb")
        _sock_send(sio, b"pong")
        assert _sock_recv(b, 4096) == b"pong"
        b.send(b"read-me")
        assert _sock_recv(sio, 4096) == b"read-me"
    finally:
        a.close()
        b.close()
