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
    executor = fake.cli.executor
    with tc.websocket_connect(
        f"/ws/containers/{CID}/logs?token={TOKEN_HASH}&follow=true"
    ) as ws:
        assert wait_for(lambda: len(executor.streams) == 1)
        stream = executor.streams[0]
        assert stream["kind"] == "container.logs"
        assert stream["stack"] == CID
        assert stream["args"] == ["docker", "logs", "-f", CID]
        assert stream["line_mode"] is True

        executor.feed(stream["task"], b"log line 1\n")
        assert ws.receive_text() == "log line 1\n"
        executor.feed(stream["task"], b"log line 2\n")
        assert ws.receive_text() == "log line 2\n"


def test_logs_ws_since_until_args(ws_client):
    tc, fake = ws_client
    executor = fake.cli.executor
    with tc.websocket_connect(
        f"/ws/containers/{CID}/logs?token={TOKEN_HASH}&since=10&until=20"
    ):
        assert wait_for(lambda: len(executor.streams) == 1)
        assert executor.streams[0]["args"] == [
            "docker", "logs", "--since", "10", "--until", "20", CID,
        ]


def test_logs_ws_error_closes_with_1011(ws_client):
    tc, fake = ws_client
    executor = fake.cli.executor
    with pytest.raises(WebSocketDisconnect) as exc:
        with tc.websocket_connect(
            f"/ws/containers/{CID}/logs?token={TOKEN_HASH}"
        ) as ws:
            assert wait_for(lambda: len(executor.streams) == 1)
            executor.finish(executor.streams[0]["task"], error="daemon gone")
            ws.receive_text()
    assert exc.value.code == 1011


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
    executor = fake.cli.executor
    ticket = create_terminal_ticket(CID, "/bin/bash")
    with tc.websocket_connect(f"/ws/terminal?ticket={ticket}") as ws:
        assert wait_for(lambda: len(executor.streams) == 1)
        stream = executor.streams[0]
        task = stream["task"]
        assert stream["kind"] == "container.terminal"
        assert stream["args"] == ["docker", "exec", "-it", CID, "/bin/bash"]

        executor.feed(task, b"$ ")
        assert ws.receive_bytes() == b"$ "

        ws.send_text("ls\n")
        assert wait_for(lambda: task.written == [b"ls\n"])

        ws.send_text(json.dumps({"rows": 24, "cols": 80}))
        assert wait_for(lambda: task.resizes == [(24, 80)])

        executor.feed(task, b"file1 file2\n$ ")
        assert ws.receive_bytes() == b"file1 file2\n$ "

        ws.send_bytes(b"\x03")
        assert wait_for(lambda: task.written[-1] == b"\x03")

        executor.finish(task)
        with pytest.raises(WebSocketDisconnect):
            ws.receive_bytes()


def test_terminal_ws_default_command(ws_client):
    tc, fake = ws_client
    executor = fake.cli.executor
    ticket = create_terminal_ticket(CID, None)
    with tc.websocket_connect(f"/ws/terminal?ticket={ticket}"):
        assert wait_for(lambda: len(executor.streams) == 1)
        assert executor.streams[0]["args"] == [
            "docker", "exec", "-it", CID, "/bin/sh",
        ]
