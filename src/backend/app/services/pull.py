import asyncio
import base64
from typing import Optional

from app.core.broadcast import manager
from app.services.cli import CliExecutor, CliTask


class PullTaskManager:
    """Broadcast image pull pty output to /ws as base64-encoded bytes."""

    def __init__(self):
        self._executors: dict[str, CliExecutor] = {}
        self._lock = asyncio.Lock()
        self._image_locks: dict[str, asyncio.Lock] = {}

    def get_executor(self, docker_host: str) -> CliExecutor:
        executor = self._executors.get(docker_host)
        if executor is None:
            executor = CliExecutor(docker_host)
            self._executors[docker_host] = executor
        return executor

    async def image_lock(self, image: str) -> asyncio.Lock:
        async with self._lock:
            return self._image_locks.setdefault(image, asyncio.Lock())

    def _make_callbacks(self, image: str):
        async def on_data(task: CliTask, data: bytes) -> None:
            await manager.broadcast({
                "type": "image.pull",
                "task_id": task.id,
                "image": image,
                "status": task.status,
                "data": base64.b64encode(data).decode("ascii"),
            })

        async def on_done(task: CliTask) -> None:
            await manager.broadcast({
                "type": "image.pull",
                "task_id": task.id,
                "image": image,
                "status": task.status,
                "returncode": task.returncode,
                "error": task.error,
            })

        return on_data, on_done

    async def start(
        self, docker_host: str, name: str, tag: Optional[str]
    ) -> Optional[CliTask]:
        """Run `docker pull` under a per-image lock; None when busy."""
        image = f"{name}:{tag}" if tag else name
        lock = await self.image_lock(image)
        if lock.locked():
            return None
        async with lock:
            on_data, on_done = self._make_callbacks(image)
            executor = self.get_executor(docker_host)
            return await executor.stream(
                "pull", image, ["docker", "pull", image],
                on_data, on_done=on_done,
            )


pull_tasks = PullTaskManager()
