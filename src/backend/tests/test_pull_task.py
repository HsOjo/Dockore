import base64

from app.services.cli import CliExecutor, CliTask
from app.services.pull import PullTaskManager


class _Recorder:
    def __init__(self):
        self.payloads = []

    async def broadcast(self, payload):
        self.payloads.append(payload)


class FakeStreamExecutor:
    """Captures stream() calls without spawning a process."""

    def __init__(self):
        self.streams = []

    async def stream(self, kind, stack, args, on_data, cwd=None,
                     on_done=None, line_mode=False):
        task = CliTask(
            id=f"pull-task-{len(self.streams)}", kind=kind, stack=stack, args=args,
        )
        self.streams.append(dict(task=task, on_data=on_data, on_done=on_done))
        return task


def _manager(monkeypatch, executor=None):
    recorder = _Recorder()
    monkeypatch.setattr("app.services.pull.manager", recorder)
    manager = PullTaskManager()
    if executor is not None:
        monkeypatch.setattr(manager, "get_executor", lambda host, proxy=None: executor)
    return manager, recorder


def test_get_executor_caches_per_host():
    manager = PullTaskManager()
    e1 = manager.get_executor("")
    assert e1 is manager.get_executor("")
    assert isinstance(e1, CliExecutor)
    assert manager.get_executor("tcp://other:2375") is not e1


async def test_start_runs_docker_pull(monkeypatch):
    executor = FakeStreamExecutor()
    manager, _ = _manager(monkeypatch, executor)
    task = await manager.start("", "nginx", "latest")
    assert task is not None
    assert task.kind == "pull"
    assert task.args == ["docker", "pull", "nginx:latest"]


async def test_start_without_tag_uses_name(monkeypatch):
    executor = FakeStreamExecutor()
    manager, _ = _manager(monkeypatch, executor)
    task = await manager.start("", "nginx", None)
    assert task.args == ["docker", "pull", "nginx"]


async def test_pull_broadcasts_progress_and_done(monkeypatch):
    executor = FakeStreamExecutor()
    manager, recorder = _manager(monkeypatch, executor)
    task = await manager.start("", "nginx", "latest")

    stream = executor.streams[0]
    await stream["on_data"](task, b"Download complete")
    payload = recorder.payloads[-1]
    assert payload["type"] == "image.pull"
    assert payload["task_id"] == task.id
    assert payload["image"] == "nginx:latest"
    assert base64.b64decode(payload["data"]) == b"Download complete"

    task.status = "done"
    task.returncode = 0
    await stream["on_done"](task)
    done = recorder.payloads[-1]
    assert done["type"] == "image.pull"
    assert done["task_id"] == task.id
    assert done["status"] == "done"
    assert done["returncode"] == 0
    assert done["error"] is None


async def test_pull_broadcasts_error(monkeypatch):
    executor = FakeStreamExecutor()
    manager, recorder = _manager(monkeypatch, executor)
    task = await manager.start("", "nginx", "latest")

    task.status = "error"
    task.returncode = 1
    task.error = "pull failed"
    await executor.streams[0]["on_done"](task)
    done = recorder.payloads[-1]
    assert done["status"] == "error"
    assert done["error"] == "pull failed"


async def test_start_returns_none_while_same_image_busy(monkeypatch):
    manager, _ = _manager(monkeypatch)

    lock = await manager.image_lock("nginx:latest")
    await lock.acquire()
    try:
        assert await manager.start("", "nginx", "latest") is None
    finally:
        lock.release()


async def test_image_lock_shared_per_image(monkeypatch):
    manager, _ = _manager(monkeypatch)
    assert await manager.image_lock("nginx:latest") is await manager.image_lock(
        "nginx:latest"
    )
    assert await manager.image_lock("redis") is not await manager.image_lock(
        "nginx:latest"
    )
