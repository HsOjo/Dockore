import asyncio
import base64
import json
from typing import Optional

from app.core.broadcast import manager
from app.core.settings_service import ProxyConfig
from app.services.cli import CliExecutor, CliTask


class StackTaskManager:
    """Broadcast stack task pty output to /ws as base64-encoded bytes."""

    def __init__(self):
        self._executors: dict[tuple[str, ProxyConfig], CliExecutor] = {}
        self._lock = asyncio.Lock()
        self._stack_locks: dict[str, asyncio.Lock] = {}

    def get_executor(
        self, docker_host: str, proxy: Optional[ProxyConfig] = None
    ) -> CliExecutor:
        key = (docker_host, proxy or ProxyConfig())
        executor = self._executors.get(key)
        if executor is None:
            executor = CliExecutor(docker_host, proxy)
            self._executors[key] = executor
        return executor

    def resize(self, task_id: str, rows: int, cols: int) -> None:
        for executor in self._executors.values():
            task = executor.get_task(task_id)
            if task is not None:
                task.resize(rows, cols)
                return

    async def stack_lock(self, name: str) -> asyncio.Lock:
        async with self._lock:
            return self._stack_locks.setdefault(name, asyncio.Lock())

    def _make_callbacks(self, kind: str, stack: str):
        async def on_data(task: CliTask, data: bytes) -> None:
            payload = {
                "type": "stack.action",
                "task_id": task.id,
                "stack": stack,
                "kind": kind,
                "status": task.status,
                "data": base64.b64encode(data).decode("ascii"),
            }
            await manager.broadcast(payload)

        async def on_done(task: CliTask) -> None:
            await manager.broadcast({
                "type": "stack.action",
                "task_id": task.id,
                "stack": stack,
                "kind": kind,
                "status": task.status,
                "returncode": task.returncode,
                "error": task.error,
            })

        return on_data, on_done

    async def start(
        self,
        executor: CliExecutor,
        kind: str,
        stack: str,
        launch,
    ) -> Optional[CliTask]:
        """Run launch(on_data, on_done) under a per-stack lock; None when busy."""
        lock = await self.stack_lock(stack)
        if lock.locked():
            return None
        async with lock:
            on_data, on_done = self._make_callbacks(kind, stack)
            return await launch(on_data, on_done)


stack_tasks = StackTaskManager()
