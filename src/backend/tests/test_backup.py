import asyncio
import io
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import StackContext, get_stack_ctx
from app.core.config import settings
from app.core.database import async_session
from app.core import stack_registry
from app.main import app
from app.services.backup import (
    BackupService,
    BindMount,
    MountPlan,
    VolumeMount,
    extract_env_files,
    parse_mounts,
)
from app.services.cli import CliExecutor, CliInfo
from app.services.stack import StackService
from tests.conftest import AUTH

CLI = CliInfo(
    command=["docker", "compose"], version="2.29.1", major=2,
    progress=True, binary="docker",
)


def test_parse_mounts_splits_named_and_bind():
    config = {
        "services": {
            "app": {
                "volumes": [
                    {"type": "volume", "source": "data", "target": "/data"},
                    {"type": "bind", "source": "/host/dir", "target": "/bind"},
                    {"type": "volume", "target": "/anon"},
                    {"type": "tmpfs", "target": "/tmp"},
                ],
            },
            "worker": {
                "volumes": [
                    {"type": "volume", "source": "data", "target": "/data"},
                    {"type": "bind", "source": "/host/dir", "target": "/bind"},
                ],
            },
        },
        "volumes": {"data": {"name": "proj_data"}},
    }
    plan = parse_mounts(config, "proj")
    assert plan.volumes == [VolumeMount(key="data", name="proj_data")]
    assert plan.binds == [BindMount(source="/host/dir", name="dir")]


def test_parse_mounts_dedupes_bind_archive_names():
    config = {
        "services": {
            "a": {"volumes": [{"type": "bind", "source": "/x/data", "target": "/a"}]},
            "b": {"volumes": [{"type": "bind", "source": "/y/data", "target": "/b"}]},
        },
    }
    plan = parse_mounts(config, "proj")
    assert [b.archive_name for b in plan.binds] == ["data", "data-2"]


def test_parse_mounts_defaults_volume_name_with_project_prefix():
    config = {
        "services": {
            "app": {"volumes": [{"type": "volume", "source": "db", "target": "/db"}]},
        },
        "volumes": {"db": None},
    }
    plan = parse_mounts(config, "proj")
    assert plan.volumes[0].name == "proj_db"


def test_parse_mounts_rejects_unsafe_volume_key():
    config = {
        "services": {
            "app": {"volumes": [{"type": "volume", "source": "a/b", "target": "/x"}]},
        },
    }
    with pytest.raises(ValueError):
        parse_mounts(config, "proj")


def test_extract_env_files(tmp_path):
    compose = tmp_path / "compose.yml"
    compose.write_text(
        "services:\n"
        "  a:\n"
        "    image: x\n"
        "    env_file: one.env\n"
        "  b:\n"
        "    image: x\n"
        "    env_file:\n"
        "      - one.env\n"
        "      - path: two.env\n"
        "        required: false\n"
    )
    refs = extract_env_files([str(compose)])
    by_path = {r.path: r for r in refs}
    assert by_path[str(tmp_path / "one.env")].required is True
    assert by_path[str(tmp_path / "two.env")].required is False
    assert len(refs) == 2


def test_helper_args_and_script(tmp_path):
    service = BackupService(container_mode=False)
    plan = MountPlan(
        volumes=[VolumeMount(key="data", name="proj_data")],
        binds=[BindMount(source="/host/dir")],
    )
    args = service.helper_args(plan, tmp_path, "proj", "20260817-000000")
    assert args[:2] == ["docker", "run"]
    assert "dockore-backup-proj-20260817-000000" in args
    mounts = [args[i + 1] for i, a in enumerate(args) if a == "-v"]
    assert "proj_data:/volumes/data:ro" in mounts
    assert "/host/dir:/binds/bind-0:ro" in mounts
    assert f"{tmp_path}:/backup" in mounts
    script = args[-1]
    assert "--numeric-owner" in script
    assert "/backup/volumes/data.tar.gz" in script
    assert "/backup/binds/dir.tar.gz" in script
    assert "warnings.txt" in script
    assert "skipped.txt" in script
    assert "/proc/mounts" in script


async def test_finalize_merges_helper_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "dockore_backups_dir", str(tmp_path / "backups"))
    service = BackupService(container_mode=False)
    backup_id, backup_dir = service.new_backup_dir("webapp")
    (backup_dir / "volumes" / "data.tar.gz").write_bytes(b"tar")
    (backup_dir / "warnings.txt").write_text("volume\tproj_data\n")
    (backup_dir / "skipped.txt").write_text("bind\t/proc\tproc\n")
    plan = MountPlan(
        volumes=[VolumeMount(key="data", name="proj_data")],
        binds=[BindMount(source="/proc")],
    )
    await service.finalize(
        backup_dir, backup_id, "webapp", True, plan, [], [],
    )
    manifest = json.loads((backup_dir / "manifest.json").read_text())
    assert manifest["volumes"] == []
    assert manifest["binds"] == []
    reasons = {(s["type"], s["ref"]): s["reason"] for s in manifest["skipped"]}
    assert "read errors" in reasons[("volume", "proj_data")]
    assert reasons[("bind", "/proc")] == "virtual filesystem (proc)"


def test_backup_dirs_and_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "dockore_backups_dir", str(tmp_path / "backups"))
    service = BackupService(container_mode=True)
    backup_id, backup_dir = service.new_backup_dir("webapp")
    second_id, _ = service.new_backup_dir("webapp")
    assert second_id != backup_id
    with pytest.raises(ValueError):
        service.resolve("webapp", "../..")
    with pytest.raises(KeyError):
        service.resolve("webapp", backup_id)
    assert service.list("webapp") == []


def test_list_skips_corrupt_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "dockore_backups_dir", str(tmp_path / "backups"))
    service = BackupService(container_mode=False)
    backup_id, backup_dir = service.new_backup_dir("webapp")
    (backup_dir / "manifest.json").write_text("not json")
    assert service.list("webapp") == []


class FakeVolumes:
    def __init__(self, existing):
        self.existing = existing

    async def item(self, name):
        return {"name": name} if name in self.existing else None


class FakeCompose:
    def __init__(self, config):
        self.cli = CLI
        self.executor = CliExecutor()
        self._config = config
        self.calls = []

    async def config_json(self, project, files, cwd):
        self.calls.append(("config", project))
        return self._config

    async def lifecycle(self, project, action, files=None, cwd=None):
        self.calls.append((project, action))


def _local_helper_args(self, plan, backup_dir, stack, backup_id):
    """Run the tar steps on the host instead of via `docker run`."""
    cmds = []
    for vol in plan.volumes:
        src = Path(vol.name)  # tests point volume names at real directories
        cmds.append(
            f"tar -czf {backup_dir}/volumes/{vol.key}.tar.gz -C {src} ."
        )
    for i, bind in enumerate(plan.binds):
        cmds.append(
            f"tar -czf {backup_dir}/binds/{bind.archive_name}.tar.gz"
            f" -C {bind.source} ."
        )
    return ["sh", "-c", "; ".join(cmds) if cmds else "true"]


@pytest.fixture
async def backup_client(tmp_path, monkeypatch):
    stack_dir = tmp_path / "webapp"
    stack_dir.mkdir()
    (stack_dir / "compose.yml").write_text(
        "services:\n"
        "  web:\n"
        "    image: nginx\n"
        "    env_file:\n"
        "      - extra.env\n"
        "      - path: optional.env\n"
        "        required: false\n"
    )
    (stack_dir / ".env").write_text("A=1\n")
    (stack_dir / "extra.env").write_text("B=2\n")
    volume_data = tmp_path / "volume-data"
    volume_data.mkdir()
    (volume_data / "dump.sql").write_text("select 1;\n")
    bind_data = tmp_path / "bind-data"
    bind_data.mkdir()
    (bind_data / "index.html").write_text("hi\n")

    monkeypatch.setattr(settings, "dockore_backups_dir", str(tmp_path / "backups"))
    monkeypatch.setattr(BackupService, "helper_args", _local_helper_args)

    scan = {
        "webapp": {
            "name": "webapp",
            "working_dir": str(stack_dir),
            "config_files": str(stack_dir / "compose.yml"),
            "containers": [
                {"id": "a", "name": "web-1", "service": "web",
                 "state": "running", "status": "Up"},
            ],
        },
    }
    docker = SimpleNamespace(
        stack=SimpleNamespace(scan=lambda: asyncio.sleep(0, scan)),
        volume=FakeVolumes({str(volume_data)}),
    )
    config = {
        "services": {
            "web": {
                "volumes": [
                    {"type": "volume", "source": "data", "target": "/d"},
                    {"type": "volume", "source": "missing", "target": "/m"},
                    {"type": "volume", "target": "/anon"},
                    {"type": "bind", "source": str(bind_data), "target": "/b"},
                ],
            },
        },
        "volumes": {
            "data": {"name": str(volume_data)},
            "missing": {"name": "webapp_missing"},
        },
    }
    compose = FakeCompose(config)
    session = async_session()
    ctx = StackContext(stack=StackService(docker), compose=compose, session=session)
    app.dependency_overrides[get_stack_ctx] = lambda: ctx
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        c.compose = compose
        c.backups_dir = tmp_path / "backups"
        yield c
    app.dependency_overrides.pop(get_stack_ctx, None)
    await session.close()


async def _wait_manifest(client: AsyncClient, backup_dir: Path):
    for _ in range(100):
        if (backup_dir / "manifest.json").is_file():
            return
        await asyncio.sleep(0.05)
    raise AssertionError("manifest.json was not written")


async def test_backup_create_list_download_delete(backup_client):
    async with async_session() as session:
        await stack_registry.register(
            session, "webapp",
            str(Path(backup_client.backups_dir).parent / "webapp"),
            str(Path(backup_client.backups_dir).parent / "webapp" / "compose.yml"),
            "created",
        )
    try:
        resp = await backup_client.post("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.status_code == 201, resp.text
        task_id = resp.json()["task_id"]

        # Full-stack lock held while the task runs.
        resp = await backup_client.post("/api/stacks/webapp/stop", headers=AUTH)
        assert resp.status_code == 409

        backup_dir = backup_client.backups_dir / "webapp"
        await _wait_manifest(backup_client, next(backup_dir.iterdir()))
        backup_id = next(backup_dir.iterdir()).name

        calls = backup_client.compose.calls
        assert ("config", "webapp") in calls
        assert ("webapp", "stop") in calls
        assert ("webapp", "start") not in calls

        resp = await backup_client.get("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        item = items[0]
        assert item["id"] == backup_id
        assert item["was_running"] is True
        assert item["compose_files"] == ["compose.yml"]
        assert sorted(item["env_files"]) == [".env", "extra.env"]
        assert [v["key"] for v in item["volumes"]] == ["data"]
        assert item["volumes"][0]["size"] > 0
        assert [b["source"] for b in item["binds"]][0].endswith("bind-data")
        assert item["binds"][0]["archive"] == "binds/bind-data.tar.gz"
        skipped = {(s["type"], s["ref"]) for s in item["skipped"]}
        assert ("volume", "webapp_missing") in skipped
        assert any(s[0] == "env_file" for s in skipped)

        resp = await backup_client.get(
            f"/api/stacks/webapp/backups/{backup_id}/download", headers=AUTH,
        )
        assert resp.status_code == 200
        with tarfile.open(fileobj=io.BytesIO(resp.content), mode="r:gz") as tar:
            names = tar.getnames()
        root = f"webapp-{backup_id}"
        assert f"{root}/manifest.json" in names
        assert f"{root}/volumes/data.tar.gz" in names

        resp = await backup_client.delete(
            f"/api/stacks/webapp/backups/{backup_id}", headers=AUTH,
        )
        assert resp.status_code == 200
        assert not (backup_dir / backup_id).exists()
        resp = await backup_client.get("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.json() == []
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "webapp")


async def test_backup_failure_removes_partial_dir(backup_client, monkeypatch):
    monkeypatch.setattr(
        BackupService, "helper_args",
        lambda self, plan, d, s, i: ["sh", "-c", "exit 1"],
    )
    stack_dir = Path(backup_client.backups_dir).parent / "webapp"
    async with async_session() as session:
        await stack_registry.register(
            session, "webapp", str(stack_dir),
            str(stack_dir / "compose.yml"), "created",
        )
    try:
        resp = await backup_client.post("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.status_code == 201
        task_id = resp.json()["task_id"]
        stack_backups = backup_client.backups_dir / "webapp"
        for _ in range(100):
            task = backup_client.compose.executor.get_task(task_id)
            leftovers = (
                [d for d in stack_backups.iterdir()]
                if stack_backups.exists() else []
            )
            if task.status != "running" and not leftovers:
                break
            await asyncio.sleep(0.05)
        assert not (
            stack_backups.exists() and any(stack_backups.iterdir())
        )
        resp = await backup_client.get("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.json() == []
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "webapp")


async def test_backup_missing_required_env_file_fails(backup_client):
    stack_dir = Path(backup_client.backups_dir).parent / "webapp"
    (stack_dir / "compose.yml").write_text(
        "services:\n  web:\n    image: nginx\n    env_file: gone.env\n"
    )
    async with async_session() as session:
        await stack_registry.register(
            session, "webapp", str(stack_dir),
            str(stack_dir / "compose.yml"), "created",
        )
    try:
        resp = await backup_client.post("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.status_code == 400
        assert "gone.env" in resp.json()["detail"]
    finally:
        async with async_session() as session:
            await stack_registry.unregister(session, "webapp")


async def test_backup_unknown_ids_return_404(backup_client):
    resp = await backup_client.get(
        "/api/stacks/webapp/backups/20260101-000000/download", headers=AUTH,
    )
    assert resp.status_code == 404
    resp = await backup_client.delete(
        "/api/stacks/webapp/backups/20260101-000000", headers=AUTH,
    )
    assert resp.status_code == 404
    resp = await backup_client.get(
        "/api/stacks/webapp/backups/..%2F..%2Fetc/download", headers=AUTH,
    )
    assert resp.status_code in (404, 422)


async def test_backup_disabled_without_backups_dir(backup_client, monkeypatch):
    monkeypatch.setattr(settings, "dockore_backups_dir", "")
    docker = SimpleNamespace(
        stack=SimpleNamespace(scan=lambda: asyncio.sleep(0, {})),
        volume=FakeVolumes(set()),
    )
    session = async_session()
    app.dependency_overrides[get_stack_ctx] = lambda: StackContext(
        stack=StackService(docker, stacks_dir="/app/stacks"),
        compose=None,
        session=session,
    )
    try:
        resp = await backup_client.get("/api/stacks/webapp/backups", headers=AUTH)
        assert resp.status_code == 503
    finally:
        await session.close()
