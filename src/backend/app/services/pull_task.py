import asyncio
import threading
import uuid
from typing import Optional

from app.core.broadcast import manager


class PullManager:
    """Run image pulls on background threads and broadcast progress events."""

    def start(self, docker, name: str, tag: Optional[str], loop: asyncio.AbstractEventLoop) -> str:
        pull_id = uuid.uuid4().hex
        thread = threading.Thread(
            target=self._run, args=(docker, name, tag, pull_id, loop), daemon=True,
        )
        thread.start()
        return pull_id

    def _emit(self, loop: asyncio.AbstractEventLoop, payload: dict):
        asyncio.run_coroutine_threadsafe(manager.broadcast(payload), loop)

    def _run(self, docker, name, tag, pull_id, loop):
        try:
            for event in docker.image.pull_stream(name, tag):
                self._emit(loop, {
                    "type": "image.pull",
                    "pull_id": pull_id,
                    "status": event.get("status"),
                    "progress": event.get("progress"),
                    "id": event.get("id"),
                })
            self._emit(loop, {
                "type": "image.pull", "pull_id": pull_id,
                "status": "done", "progress": None, "id": None,
            })
        except Exception as e:
            self._emit(loop, {
                "type": "image.pull", "pull_id": pull_id,
                "status": "error", "progress": None, "id": None, "error": str(e),
            })


pull_manager = PullManager()
