import asyncio
import os
import shutil
import subprocess
from pathlib import Path
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
from app.services import git as git_service
from app.services.cli import CliError, CliExecutor, CliInfo
from app.services.cli.stack import StackDiscovery, parse_labels
from app.services.compose.service import parse_json_output
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


def test_parse_labels():
    labels = parse_labels(
        "com.docker.compose.project=webapp,com.docker.compose.service=web"
    )
    assert labels == {
        "com.docker.compose.project": "webapp",
        "com.docker.compose.service": "web",
    }
    assert parse_labels("") == {}
    # 值中含逗号时续接到上一个 key
    labels = parse_labels("a=x,y,b=1")
    assert labels == {"a": "x,y", "b": "1"}


class FakePsCli:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def run_json_lines(self, *args):
        self.calls.append(args)
        return self.rows


def make_ps_cli():
    return FakePsCli([
        {
            "ID": "a" * 64, "Names": "web-1", "State": "running",
            "Status": "Up 2 hours",
            "Labels": (
                "com.docker.compose.project=webapp,"
                "com.docker.compose.project.working_dir=/srv/webapp,"
                "com.docker.compose.project.config_files=/srv/webapp/compose.yml,"
                "com.docker.compose.service=web"
            ),
        },
        {
            "ID": "b" * 64, "Names": "web-2", "State": "exited",
            "Status": "Exited (0)",
            "Labels": (
                "com.docker.compose.project=webapp,"
                "com.docker.compose.project.working_dir=/srv/webapp,"
                "com.docker.compose.project.config_files=/srv/webapp/compose.yml,"
                "com.docker.compose.service=worker"
            ),
        },
        {"ID": "c" * 64, "Names": "plain", "State": "running",
         "Status": "Up", "Labels": ""},
    ])


async def test_discovery_scan_groups_by_project():
    cli = make_ps_cli()
    stacks = await StackDiscovery(cli).scan()
    assert cli.calls == [("ps", "-a", "--no-trunc", "--format", "{{json .}}")]
    assert set(stacks) == {"webapp"}
    entry = stacks["webapp"]
    assert entry["working_dir"] == "/srv/webapp"
    assert entry["config_files"] == "/srv/webapp/compose.yml"
    assert len(entry["containers"]) == 2
    assert entry["containers"][0]["service"] == "web"
    assert entry["containers"][0]["id"] == "a" * 12
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


def test_resolve_register_target(tmp_path):
    stacks_dir = tmp_path / "stacks"
    stack_dir = stacks_dir / "alpha"
    stack_dir.mkdir(parents=True)
    compose = stack_dir / "compose.yml"
    compose.write_text("services: {}")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "compose.yml").write_text("services: {}")
    no_compose = stacks_dir / "empty"
    no_compose.mkdir()

    container = StackService(fake_docker({}), stacks_dir=str(stacks_dir))
    resolved_dir, files = container.resolve_register_target(str(stack_dir))
    assert resolved_dir == stack_dir
    assert files == [compose]
    with pytest.raises(ValueError, match="outside stacks_dir"):
        container.resolve_register_target(str(outside))
    with pytest.raises(ValueError, match="not found"):
        container.resolve_register_target(str(stacks_dir / "nope"))
    with pytest.raises(ValueError, match="No compose file"):
        container.resolve_register_target(str(no_compose))

    desktop = StackService(fake_docker({}))
    resolved_dir, files = desktop.resolve_register_target(str(outside))
    assert resolved_dir == outside
    assert files == [outside / "compose.yml"]


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
        self, project, on_data, files=None, cwd=None, follow=True, tail="200",
        since=None, until=None, on_done=None,
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


async def test_api_lifecycle_calls_compose(stack_client):
    resp = await stack_client.post("/api/stacks/webapp/restart", headers=AUTH)
    assert resp.status_code == 200
    assert stack_client.compose.calls == [("webapp", "restart")]


async def test_api_file_guard_blocks_unregistered(stack_client):
    resp = await stack_client.get("/api/stacks/webapp/file", headers=AUTH)
    assert resp.status_code == 403


async def test_api_stack_not_found(stack_client):
    resp = await stack_client.get("/api/stacks/nope", headers=AUTH)
    assert resp.status_code == 404


@pytest.fixture
async def register_client(tmp_path):
    stacks_dir = tmp_path / "stacks"
    compose_file = stacks_dir / "alpha" / "compose.yml"
    compose_file.parent.mkdir(parents=True)
    compose_file.write_text("services: {}")
    compose = FakeComposeService()
    session = async_session()
    app.dependency_overrides[get_stack_ctx] = lambda: make_ctx(
        compose, session, stacks_dir=str(stacks_dir),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        c.compose = compose
        c.stacks_dir = stacks_dir
        c.compose_file = compose_file
        yield c
    app.dependency_overrides.pop(get_stack_ctx, None)
    async with async_session() as cleanup:
        await stack_registry.unregister(cleanup, "alpha")
    await compose.close()
    await session.close()


async def test_api_register_candidates_container_mode(register_client):
    resp = await register_client.get("/api/stacks/register/candidates", headers=AUTH)
    assert resp.status_code == 404


async def test_api_register_stack_container_mode(register_client):
    stack_dir = register_client.compose_file.parent
    resp = await register_client.post("/api/stacks/register", headers=AUTH, json={
        "name": "alpha",
        "path": str(stack_dir),
    })
    assert resp.status_code == 200
    resp = await register_client.get("/api/stacks/alpha", headers=AUTH)
    assert resp.status_code == 200
    item = resp.json()
    assert item["registered"] and item["source"] == "registered"
    assert item["config_files"] == [str(register_client.compose_file)]
    assert item["file_accessible"]

    resp = await register_client.post("/api/stacks/register", headers=AUTH, json={
        "name": "alpha",
        "path": str(stack_dir),
    })
    assert resp.status_code == 409


async def test_api_register_outside_stacks_dir_rejected(register_client, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "compose.yml").write_text("services: {}")
    resp = await register_client.post("/api/stacks/register", headers=AUTH, json={
        "name": "rogue",
        "path": str(outside),
    })
    assert resp.status_code == 400
    assert "outside stacks_dir" in resp.json()["detail"]


@pytest.fixture
async def import_client(tmp_path):
    stacks_dir = tmp_path / "stacks"
    stack_dir = stacks_dir / "rel"
    stack_dir.mkdir(parents=True)
    (stack_dir / "compose.yml").write_text("services: {}")
    scan_data = {
        "rel": {
            "name": "rel",
            "working_dir": str(stack_dir),
            "config_files": "compose.yml",
            "containers": [
                {"id": "e", "name": "rel-app-1", "service": "app",
                 "state": "running", "status": "Up"},
            ],
        },
    }
    compose = FakeComposeService()
    session = async_session()
    app.dependency_overrides[get_stack_ctx] = lambda: StackContext(
        stack=StackService(fake_docker(scan_data), stacks_dir=str(stacks_dir)),
        compose=compose,
        session=session,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        c.stack_dir = stack_dir
        yield c
    app.dependency_overrides.pop(get_stack_ctx, None)
    async with async_session() as cleanup:
        await stack_registry.unregister(cleanup, "rel")
    await compose.close()
    await session.close()


async def test_api_import_relative_config_files(import_client):
    resp = await import_client.get("/api/stacks/rel", headers=AUTH)
    assert resp.status_code == 200
    item = resp.json()
    assert item["config_files"] == [str(import_client.stack_dir / "compose.yml")]
    assert item["file_accessible"]

    resp = await import_client.post(
        "/api/stacks/import", headers=AUTH, json={"name": "rel"},
    )
    assert resp.status_code == 200
    resp = await import_client.get("/api/stacks/rel", headers=AUTH)
    item = resp.json()
    assert item["registered"] and item["source"] == "imported"


async def test_api_register_desktop_mode(stack_client, tmp_path):
    stack_dir = tmp_path / "anywhere" / "beta"
    stack_dir.mkdir(parents=True)
    (stack_dir / "compose.yml").write_text("services: {}")

    resp = await stack_client.post("/api/stacks/register", headers=AUTH, json={
        "name": "beta", "path": str(stack_dir),
    })
    assert resp.status_code == 200
    async with async_session() as cleanup:
        await stack_registry.unregister(cleanup, "beta")


async def test_api_register_missing_file(stack_client, tmp_path):
    stack_dir = tmp_path / "beta"
    stack_dir.mkdir()
    resp = await stack_client.post("/api/stacks/register", headers=AUTH, json={
        "name": "beta",
        "path": str(stack_dir),
    })
    assert resp.status_code == 400


async def test_api_register_discovered_unregistered(stack_client, tmp_path):
    stack_dir = tmp_path / "webapp"
    stack_dir.mkdir()
    (stack_dir / "compose.yml").write_text("services: {}")
    resp = await stack_client.post("/api/stacks/register", headers=AUTH, json={
        "name": "webapp", "path": str(stack_dir),
    })
    assert resp.status_code == 200
    resp = await stack_client.get("/api/stacks/webapp", headers=AUTH)
    item = resp.json()
    assert item["registered"] and item["source"] == "registered"
    assert item["status"] == "running"
    async with async_session() as cleanup:
        await stack_registry.unregister(cleanup, "webapp")


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


async def test_api_env_read_missing_returns_empty(env_client):
    resp = await env_client.get("/api/stacks/realapp/env", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == ""
    assert data["path"].endswith(".env")


async def test_api_env_write_creates_and_backs_up(env_client):
    resp = await env_client.put(
        "/api/stacks/realapp/env", headers=AUTH, json={"content": "A=1\n"},
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is True
    assert env_client.env_path.read_text() == "A=1\n"
    backup = env_client.env_path.parent / ".env.bak"
    assert not backup.exists()

    resp = await env_client.put(
        "/api/stacks/realapp/env", headers=AUTH, json={"content": "A=2\n"},
    )
    assert resp.status_code == 200
    assert backup.read_text() == "A=1\n"
    assert ("validate", ["{}".format(env_client.env_path.parent / "compose.yml")],
            str(env_client.env_path.parent)) in env_client.compose.calls


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


async def test_api_env_guard_blocks_unregistered(stack_client):
    resp = await stack_client.get("/api/stacks/webapp/env", headers=AUTH)
    assert resp.status_code == 403


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


def test_git_scan_candidates_nested(tmp_path):
    (tmp_path / "docker-compose.yml").write_text("services: {}")
    deploy = tmp_path / "deploy" / "app"
    deploy.mkdir(parents=True)
    (deploy / "compose.yaml").write_text("services: {}")
    (deploy / ".env.example").write_text("A=1\n")
    (deploy / "app.env.template").write_text("B=2\n")
    (tmp_path / "README.md").write_text("hi")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "compose.yml").write_text("ignored")

    composes, env_templates = git_service.scan_candidates(tmp_path)
    assert composes == ["deploy/app/compose.yaml", "docker-compose.yml"]
    assert env_templates == ["deploy/app/.env.example", "deploy/app/app.env.template"]


def test_git_resolve_in_repo_blocks_traversal(tmp_path):
    assert git_service.resolve_in_repo(tmp_path, "a/b.yml") == tmp_path / "a/b.yml"
    with pytest.raises(ValueError):
        git_service.resolve_in_repo(tmp_path, "../outside.yml")
    with pytest.raises(ValueError):
        git_service.resolve_in_repo(tmp_path, "/etc/passwd")


GIT_REQUIRED = pytest.mark.skipif(
    shutil.which("git") is None, reason="git CLI required",
)


def _init_git_repo(path: Path) -> None:
    path.mkdir(parents=True)
    env = {
        "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@test",
        "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@test",
        "PATH": os.environ.get("PATH", ""),
    }

    def run(*args):
        subprocess.run(
            ["git", "-C", str(path), *args], check=True,
            capture_output=True, env=env,
        )

    run("init", "-b", "main")
    deploy = path / "deploy"
    deploy.mkdir()
    (deploy / "compose.yml").write_text("services:\n  app:\n    image: nginx\n")
    (deploy / ".env.example").write_text("A=1\n")
    (path / "docker-compose.yml").write_text("services:\n  root:\n    image: nginx\n")
    run("add", "-A")
    run("commit", "-m", "init")


@pytest.fixture
async def git_client(tmp_path):
    compose = FakeComposeService()
    session = async_session()
    stacks_base = tmp_path / "stacks"
    stacks_base.mkdir()
    app.dependency_overrides[get_stack_ctx] = lambda: StackContext(
        stack=StackService(fake_docker({})), compose=compose, session=session,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        c.compose = compose
        c.stacks_base = stacks_base
        yield c
    app.dependency_overrides.pop(get_stack_ctx, None)
    await compose.close()
    await session.close()


async def _run_clone(client, name, repo, directory):
    resp = await client.post("/api/stacks/git/clone", headers=AUTH, json={
        "name": name, "repo_url": str(repo), "directory": directory,
    })
    assert resp.status_code == 200
    task = client.compose.executor.get_task(resp.json()["task_id"])
    for _ in range(50):
        if task.status != "running":
            break
        await asyncio.sleep(0.1)
    return task


async def _wait_dir_gone(path):
    for _ in range(30):
        if not path.exists():
            break
        await asyncio.sleep(0.1)


@GIT_REQUIRED
async def test_api_git_clone_and_create(git_client, tmp_path):
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    directory = str(git_client.stacks_base)

    task = await _run_clone(git_client, "gitapp", repo, directory)
    assert task.status == "done"
    assert (git_client.stacks_base / "gitapp" / ".git").is_dir()

    resp = await git_client.get(
        "/api/stacks/git/candidates", headers=AUTH,
        params={"name": "gitapp", "directory": directory},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["compose_files"] == ["deploy/compose.yml", "docker-compose.yml"]
    assert data["env_templates"] == ["deploy/.env.example"]

    resp = await git_client.get(
        "/api/stacks/git/file", headers=AUTH,
        params={"name": "gitapp", "path": "deploy/compose.yml",
                "directory": directory},
    )
    assert resp.status_code == 200
    assert resp.json()["content"].startswith("services:")

    try:
        resp = await git_client.post("/api/stacks/git/create", headers=AUTH, json={
            "name": "gitapp",
            "compose_path": "deploy/compose.yml",
            "content": "services:\n  app:\n    image: nginx:alpine\n",
            "env": "A=9\n",
            "directory": directory,
        })
        assert resp.status_code == 201
        assert resp.json()["task_id"]
        stack_dir = git_client.stacks_base / "gitapp"
        compose_file = stack_dir / "deploy" / "compose.yml"
        assert compose_file.read_text() == "services:\n  app:\n    image: nginx:alpine\n"
        assert (stack_dir / "deploy" / ".env").read_text() == "A=9\n"
        async with async_session() as session:
            reg = await stack_registry.get(session, "gitapp")
        assert reg is not None and reg.source == "git"
        assert reg.config_files == str(compose_file)
        assert ("up", "gitapp", [str(compose_file)],
                str(compose_file.parent)) in git_client.compose.calls
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "gitapp")


@GIT_REQUIRED
async def test_api_git_create_copies_env_template(git_client, tmp_path):
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    directory = str(git_client.stacks_base)
    task = await _run_clone(git_client, "gitapp", repo, directory)
    assert task.status == "done"

    try:
        resp = await git_client.post("/api/stacks/git/create", headers=AUTH, json={
            "name": "gitapp",
            "compose_path": "deploy/compose.yml",
            "env_template_path": "deploy/.env.example",
            "directory": directory,
        })
        assert resp.status_code == 201
        stack_dir = git_client.stacks_base / "gitapp"
        assert (stack_dir / "deploy" / ".env").read_text() == "A=1\n"
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "gitapp")


@GIT_REQUIRED
async def test_api_git_clone_invalid_repo_cleans_up(git_client, tmp_path):
    resp = await git_client.post("/api/stacks/git/clone", headers=AUTH, json={
        "name": "badrepo", "repo_url": str(tmp_path / "nope"),
        "directory": str(git_client.stacks_base),
    })
    assert resp.status_code == 200
    task = git_client.compose.executor.get_task(resp.json()["task_id"])
    for _ in range(50):
        if task.status != "running":
            break
        await asyncio.sleep(0.1)
    assert task.status == "error"
    await _wait_dir_gone(git_client.stacks_base / "badrepo")
    assert not (git_client.stacks_base / "badrepo").exists()


@GIT_REQUIRED
async def test_api_git_create_rejects_traversal(git_client, tmp_path):
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    directory = str(git_client.stacks_base)
    task = await _run_clone(git_client, "gitapp", repo, directory)
    assert task.status == "done"

    resp = await git_client.post("/api/stacks/git/create", headers=AUTH, json={
        "name": "gitapp", "compose_path": "../repo/docker-compose.yml",
        "directory": directory,
    })
    assert resp.status_code == 400

    resp = await git_client.get(
        "/api/stacks/git/file", headers=AUTH,
        params={"name": "gitapp", "path": "../repo/docker-compose.yml",
                "directory": directory},
    )
    assert resp.status_code == 400


@GIT_REQUIRED
async def test_api_git_cancel_removes_clone(git_client, tmp_path):
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    directory = str(git_client.stacks_base)
    task = await _run_clone(git_client, "gitapp", repo, directory)
    assert task.status == "done"

    resp = await git_client.post("/api/stacks/git/cancel", headers=AUTH, json={
        "name": "gitapp", "directory": directory,
    })
    assert resp.status_code == 200
    assert not (git_client.stacks_base / "gitapp").exists()


@GIT_REQUIRED
async def test_api_git_cancel_refuses_registered(git_client, tmp_path):
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    directory = str(git_client.stacks_base)
    task = await _run_clone(git_client, "gitapp", repo, directory)
    assert task.status == "done"
    async with async_session() as session:
        await stack_registry.register(
            session, "gitapp", str(git_client.stacks_base / "gitapp"),
            str(git_client.stacks_base / "gitapp" / "docker-compose.yml"), "git",
        )
    try:
        resp = await git_client.post("/api/stacks/git/cancel", headers=AUTH, json={
            "name": "gitapp", "directory": directory,
        })
        assert resp.status_code == 409
        assert (git_client.stacks_base / "gitapp").exists()
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "gitapp")
