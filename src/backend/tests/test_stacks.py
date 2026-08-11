import asyncio
from types import SimpleNamespace

import pytest
import time
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.api.deps import StackContext, get_stack_ctx
from app.core.database import async_session, get_db
from app.core import stack_registry
from app.main import app
from app.services.cli import CliError, CliExecutor, CliInfo
from app.services.compose.service import parse_json_output
from app.services.docker.stack import StackDiscovery
from app.services.stack import StackService, derive_status
from tests.conftest import AUTH, TOKEN_HASH

CLI = CliInfo(
    command=["docker", "compose"], version="2.29.1", major=2,
    progress=True, binary="docker",
)


def test_derive_status():
    assert derive_status([]) == "inactive"
    assert derive_status([{"state": "running"}]) == "running"
    assert derive_status([{"state": "exited"}]) == "stopped"
    assert derive_status([{"state": "running"}, {"state": "exited"}]) == "partial"


class FakeApi:
    def containers(self, all=False):
        return [
            {
                "Id": "a" * 64, "Names": ["/web-1"], "State": "running",
                "Status": "Up 2 hours",
                "Labels": {
                    "com.docker.compose.project": "webapp",
                    "com.docker.compose.project.working_dir": "/srv/webapp",
                    "com.docker.compose.project.config_files": "/srv/webapp/compose.yml",
                    "com.docker.compose.service": "web",
                },
            },
            {
                "Id": "b" * 64, "Names": ["/web-2"], "State": "exited",
                "Status": "Exited (0)",
                "Labels": {
                    "com.docker.compose.project": "webapp",
                    "com.docker.compose.project.working_dir": "/srv/webapp",
                    "com.docker.compose.project.config_files": "/srv/webapp/compose.yml",
                    "com.docker.compose.service": "worker",
                },
            },
            {"Id": "c" * 64, "Names": ["/plain"], "State": "running",
             "Status": "Up", "Labels": {}},
        ]


async def test_discovery_scan_groups_by_project():
    stacks = await StackDiscovery(FakeApi()).scan()
    assert set(stacks) == {"webapp"}
    entry = stacks["webapp"]
    assert entry["working_dir"] == "/srv/webapp"
    assert entry["config_files"] == "/srv/webapp/compose.yml"
    assert len(entry["containers"]) == 2
    assert entry["containers"][0]["service"] == "web"
    assert entry["containers"][1]["state"] == "exited"


def fake_docker(scan_data):
    discovery = SimpleNamespace(scan=lambda: asyncio.sleep(0, scan_data))
    return SimpleNamespace(stack=discovery)


SCAN_DATA = {
    "webapp": {
        "name": "webapp",
        "working_dir": "/srv/webapp",
        "config_files": "/srv/webapp/compose.yml",
        "containers": [
            {"id": "a", "name": "web-1", "service": "web",
             "state": "running", "status": "Up"},
        ],
    },
}


def make_reg(name, path, config_files, source="created"):
    return SimpleNamespace(
        name=name, path=path, config_files=config_files, source=source,
    )


async def test_stack_service_merges_discovery_and_registry(tmp_path):
    service = StackService(fake_docker(SCAN_DATA))
    regs = [
        make_reg("webapp", "/srv/webapp", "/srv/webapp/compose.yml", "imported"),
        make_reg("ghost", str(tmp_path), str(tmp_path / "compose.yml")),
        make_reg("gone", str(tmp_path / "nope"), str(tmp_path / "nope/compose.yml")),
    ]
    items = {i["name"]: i for i in await service.list(regs)}

    web = items["webapp"]
    assert web["status"] == "running"
    assert web["registered"] and web["source"] == "imported"
    assert web["file_accessible"]

    assert items["ghost"]["status"] == "inactive"
    assert items["gone"]["status"] == "missing"
    assert not items["gone"]["file_accessible"]


async def test_stack_service_container_mode_file_matrix(tmp_path):
    stacks_dir = tmp_path / "stacks"
    stacks_dir.mkdir()
    inside = stacks_dir / "app" / "compose.yml"
    inside.parent.mkdir()
    inside.write_text("services: {}")
    service = StackService(fake_docker({}), stacks_dir=str(stacks_dir))

    assert service.container_mode
    assert service.file_accessible([str(inside)], registered=False)
    assert not service.file_accessible(["/etc/passwd"], registered=True)
    assert not service.file_accessible([], registered=True)

    desktop = StackService(fake_docker({}))
    assert not desktop.container_mode
    assert desktop.file_accessible(["/anywhere/compose.yml"], registered=True)
    assert not desktop.file_accessible(["/anywhere/compose.yml"], registered=False)


def test_resolve_create_target(tmp_path):
    container = StackService(fake_docker({}), stacks_dir=str(tmp_path))
    stack_dir, compose_file = container.resolve_create_target("demo")
    assert stack_dir == tmp_path / "demo"
    assert compose_file == stack_dir / "compose.yml"

    desktop = StackService(fake_docker({}))
    stack_dir, _ = desktop.resolve_create_target("demo", directory=str(tmp_path))
    assert stack_dir == tmp_path / "demo"
    with pytest.raises(ValueError):
        desktop.resolve_create_target("demo")


def test_parse_json_output():
    assert parse_json_output("") == []
    assert parse_json_output('[{"Name": "a"}]') == [{"Name": "a"}]
    assert parse_json_output('{"a": 1}\n{"b": 2}') == [{"a": 1}, {"b": 2}]


async def test_cli_executor_run_ok():
    out = await CliExecutor().run(["sh", "-c", "echo hi"])
    assert out.strip() == "hi"


async def test_cli_executor_run_failure_raises():
    with pytest.raises(CliError) as exc:
        await CliExecutor().run(["sh", "-c", "echo boom; exit 3"])
    assert exc.value.returncode == 3
    assert "boom" in exc.value.output


async def test_cli_executor_stream_and_cancel():
    chunks = []

    async def on_data(task, data):
        chunks.append(data)

    executor = CliExecutor()
    task = await executor.stream(
        "up", "demo", ["sh", "-c", "echo first; sleep 30"], on_data,
    )
    await asyncio.sleep(0.5)
    assert await executor.cancel(task.id)
    for _ in range(30):
        if task.status != "running":
            break
        await asyncio.sleep(0.1)
    assert task.status == "cancelled"
    assert any(b"first" in chunk for chunk in chunks)
    await asyncio.sleep(0.3)


class FakeComposeService:
    def __init__(self):
        self.cli = CLI
        self.executor = CliExecutor()
        self.calls = []
        self._tasks = []
        self.down_command = ["sh", "-c", "true"]

    async def close(self):
        for task in self._tasks:
            if task.status == "running":
                await self.executor.cancel(task.id)
        if self._tasks:
            await asyncio.gather(
                *[self._wait(task) for task in self._tasks], return_exceptions=True,
            )

    async def _wait(self, task):
        while task.status == "running":
            await asyncio.sleep(0.05)

    async def lifecycle(self, project, action, files=None, cwd=None):
        self.calls.append((project, action))

    async def validate(self, files, cwd):
        self.calls.append(("validate", files, cwd))

    async def up(self, project, files, cwd, on_data, on_done=None):
        self.calls.append(("up", project, files, cwd))
        task = await self.executor.stream(
            "up", project, ["sh", "-c", "true"], _text_to_data(on_data), on_done=on_done,
        )
        self._tasks.append(task)
        return task

    async def down(self, project, remove_volumes, on_data, on_done=None):
        self.calls.append(("down", project, remove_volumes))
        task = await self.executor.stream(
            "down", project, self.down_command, _text_to_data(on_data), on_done=on_done,
        )
        self._tasks.append(task)
        return task

    async def logs(
        self, project, on_data, files=None, cwd=None, follow=True, tail="200", on_done=None,
    ):
        self.calls.append(("logs", project, files, cwd))
        return await self.executor.stream(
            "logs", project, ["sh", "-c", "echo line1; echo line2; sleep 30"],
            on_data, cwd=cwd, on_done=on_done, line_mode=True,
        )

    async def pull(self, project, files, cwd, on_data, on_done=None):
        self.calls.append(("pull", project, files, cwd))
        task = await self.executor.stream(
            "pull", project, ["sh", "-c", "true"], _text_to_data(on_data), on_done=on_done,
        )
        self._tasks.append(task)
        return task


def _text_to_data(on_data):
    async def on_line(task, line):
        await on_data(task, (line + "\n").encode())
    return on_line


def make_ctx(compose, session, stacks_dir=""):
    return StackContext(
        stack=StackService(fake_docker(SCAN_DATA), stacks_dir=stacks_dir),
        compose=compose,
        session=session,
    )


@pytest.fixture
async def stack_client():
    compose = FakeComposeService()
    session = async_session()
    app.dependency_overrides[get_stack_ctx] = lambda: make_ctx(compose, session)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        c.compose = compose
        yield c
    app.dependency_overrides.pop(get_stack_ctx, None)
    await compose.close()
    await session.close()


async def test_api_meta(stack_client):
    resp = await stack_client.get("/api/stacks/meta", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["cli_available"] and data["cli_version"] == "2.29.1"
    assert data["container_mode"] is False


async def test_api_list_stacks(stack_client):
    async with async_session() as session:
        await stack_registry.register(
            session, "webapp", "/srv/webapp", "/srv/webapp/compose.yml", "imported",
        )
    try:
        resp = await stack_client.get("/api/stacks", headers=AUTH)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["name"] == "webapp"
        assert items[0]["registered"] and items[0]["source"] == "imported"
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "webapp")


async def test_api_stack_not_found(stack_client):
    resp = await stack_client.get("/api/stacks/nope", headers=AUTH)
    assert resp.status_code == 404


@pytest.fixture
async def env_client(tmp_path):
    compose_file = tmp_path / "realapp" / "compose.yml"
    compose_file.parent.mkdir()
    compose_file.write_text("services:\n  app:\n    image: nginx\n")
    scan_data = {
        "realapp": {
            "name": "realapp",
            "working_dir": str(tmp_path / "realapp"),
            "config_files": str(compose_file),
            "containers": [
                {"id": "d", "name": "realapp-app-1", "service": "app",
                 "state": "running", "status": "Up"},
            ],
        },
    }
    compose = FakeComposeService()
    session = async_session()
    await stack_registry.register(
        session, "realapp", str(tmp_path / "realapp"), str(compose_file), "created",
    )
    app.dependency_overrides[get_stack_ctx] = lambda: StackContext(
        stack=StackService(fake_docker(scan_data)),
        compose=compose,
        session=session,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        c.compose = compose
        c.env_path = tmp_path / "realapp" / ".env"
        yield c
    app.dependency_overrides.pop(get_stack_ctx, None)
    async with async_session() as cleanup:
        await stack_registry.unregister(cleanup, "realapp")
    await compose.close()
    await session.close()


async def test_api_destroy_registered_stack(env_client):
    resp = await env_client.post(
        "/api/stacks/realapp/destroy", headers=AUTH,
        json={"remove_volumes": False, "delete_files": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"]
    # poll for the async cleanup task
    for _ in range(20):
        await asyncio.sleep(0.1)
        async with async_session() as session:
            reg = await stack_registry.get(session, "realapp")
        if reg is None and not env_client.env_path.parent.exists():
            break
    async with async_session() as session:
        assert await stack_registry.get(session, "realapp") is None
    assert not env_client.env_path.parent.exists()


async def test_api_destroy_failed_down_keeps_registration_and_files(env_client):
    env_client.compose.down_command = ["sh", "-c", "exit 1"]
    resp = await env_client.post(
        "/api/stacks/realapp/destroy", headers=AUTH,
        json={"remove_volumes": False, "delete_files": True},
    )
    assert resp.status_code == 200
    task = env_client.compose._tasks[-1]
    for _ in range(30):
        if task.status != "running":
            break
        await asyncio.sleep(0.1)
    assert task.status == "error"
    await asyncio.sleep(0.2)
    async with async_session() as session:
        assert await stack_registry.get(session, "realapp") is not None
    assert env_client.env_path.parent.exists()


async def test_api_create_stack_writes_compose_and_env(tmp_path):
    compose = FakeComposeService()
    session = async_session()
    app.dependency_overrides[get_stack_ctx] = lambda: StackContext(
        stack=StackService(fake_docker({})), compose=compose, session=session,
    )
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            resp = await c.post("/api/stacks", headers=AUTH, json={
                "name": "newapp",
                "content": "services:\n  app:\n    image: nginx\n",
                "directory": str(tmp_path),
                "env": "A=1\n",
            })
            assert resp.status_code == 201
            assert resp.json()["task_id"]
            stack_dir = tmp_path / "newapp"
            assert (stack_dir / "compose.yml").read_text().startswith("services:")
            assert (stack_dir / ".env").read_text() == "A=1\n"
            assert await stack_registry.get(session, "newapp") is not None
            assert ("up", "newapp", [str(stack_dir / "compose.yml")],
                    str(stack_dir)) in compose.calls
    finally:
        app.dependency_overrides.pop(get_stack_ctx, None)
        await compose.close()
        await session.close()


async def _cleanup_stack_ws(compose, session):
    await compose.close()
    await session.close()


def test_stack_logs_ws_streams_bytes(tmp_path):
    compose = FakeComposeService()
    session = async_session()
    stack_dir = tmp_path / "webapp"
    stack_dir.mkdir()
    compose_file = stack_dir / "compose.yml"
    compose_file.write_text("services:\n  app:\n    image: nginx\n")

    async def _override(session: AsyncSession = Depends(get_db)):
        return StackContext(
            stack=StackService(fake_docker(SCAN_DATA)),
            compose=compose,
            session=session,
        )

    app.dependency_overrides[get_stack_ctx] = _override
    try:
        # Register the webapp stack so file_accessible is true.
        asyncio.run(
            stack_registry.register(
                session, "webapp", str(stack_dir), str(compose_file), "imported",
            )
        )
        with TestClient(app) as tc:
            with tc.websocket_connect(
                f"/ws/stacks/webapp/logs?token={TOKEN_HASH}&follow=true"
            ) as ws:
                received: list[bytes] = []
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline and len(received) < 2:
                    data = ws.receive_bytes()
                    received.append(data)
                    if any(b"line2" in chunk for chunk in received):
                        break
                assert any(b"line1" in chunk for chunk in received)
                assert any(b"line2" in chunk for chunk in received)
    finally:
        app.dependency_overrides.pop(get_stack_ctx, None)
        asyncio.run(_cleanup_stack_ws(compose, session))
