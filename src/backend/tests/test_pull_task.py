import asyncio
from types import SimpleNamespace

from app.services.pull_task import PullManager
from tests.fakes import FakeImageService


class _Recorder:
    def __init__(self):
        self.payloads = []

    async def broadcast(self, payload):
        self.payloads.append(payload)


async def _run_pull(manager, docker, monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr("app.services.pull_task.manager", recorder)
    loop = asyncio.get_running_loop()
    pull_id = manager.start(docker, "nginx", "latest", loop)
    for _ in range(200):
        if any(p.get("status") in ("done", "error") for p in recorder.payloads):
            break
        await asyncio.sleep(0.02)
    return pull_id, recorder.payloads


async def test_pull_broadcasts_progress_and_done(monkeypatch):
    docker = SimpleNamespace(image=FakeImageService())
    pull_id, payloads = await _run_pull(PullManager(), docker, monkeypatch)

    assert payloads[0] == {
        "type": "image.pull",
        "pull_id": pull_id,
        "status": "Pulling from library/nginx",
        "progress": None,
        "id": None,
    }
    assert payloads[1]["status"] == "Download complete"
    assert payloads[1]["progress"] == "100%"
    assert payloads[-1] == {
        "type": "image.pull",
        "pull_id": pull_id,
        "status": "done",
        "progress": None,
        "id": None,
    }


async def test_pull_broadcasts_error(monkeypatch):
    class _BadImage:
        def pull_stream(self, name, tag):
            raise RuntimeError("pull failed")

    docker = SimpleNamespace(image=_BadImage())
    pull_id, payloads = await _run_pull(PullManager(), docker, monkeypatch)

    assert payloads[-1]["type"] == "image.pull"
    assert payloads[-1]["pull_id"] == pull_id
    assert payloads[-1]["status"] == "error"
    assert "pull failed" in payloads[-1]["error"]
