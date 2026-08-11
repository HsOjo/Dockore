import asyncio
import os
import re
import signal
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from .env import build_env

CANCEL_GRACE_SECONDS = 5
FINISHED_TASKS_KEPT = 50


class CliError(Exception):
    def __init__(self, args: list[str], returncode: int, output: str):
        self.args = args
        self.returncode = returncode
        self.output = output
        super().__init__(
            f"command failed ({returncode}): {' '.join(args)}\n{output.strip()}"
        )


@dataclass
class CliTask:
    id: str
    kind: str
    stack: str
    args: list[str]
    status: str = "running"
    returncode: Optional[int] = None
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    _proc: Optional[asyncio.subprocess.Process] = field(default=None, repr=False)
    _master_fd: Optional[int] = field(default=None, repr=False)

    def resize(self, rows: int, cols: int) -> None:
        if self._master_fd is None or os.name == "nt":
            return
        try:
            import fcntl
            import struct
            import termios

            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, winsize)
        except OSError:
            pass


BytesCallback = Callable[[CliTask, bytes], Awaitable[None]]
DoneCallback = Callable[[CliTask], Awaitable[None]]


class CliExecutor:
    """Async subprocess runner backed by a pty when possible.

    stdout/stderr are forwarded as raw bytes so the frontend xterm can render
    the real terminal behaviour (\r overwrite, ANSI colours, etc.).
    """

    def __init__(self, docker_host: str = ""):
        self._env = build_env(docker_host)
        self.tasks: dict[str, CliTask] = {}

    async def run(self, args: list[str], cwd: Optional[str] = None) -> str:
        proc = await asyncio.create_subprocess_exec(
            *args, cwd=cwd, env=self._env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        text = out.decode(errors="ignore")
        if proc.returncode != 0:
            raise CliError(args, proc.returncode or -1, text)
        return text

    async def stream(
        self,
        kind: str,
        stack: str,
        args: list[str],
        on_data: BytesCallback,
        cwd: Optional[str] = None,
        on_done: Optional[DoneCallback] = None,
        line_mode: bool = False,
    ) -> CliTask:
        task = CliTask(id=uuid.uuid4().hex, kind=kind, stack=stack, args=args)
        self.tasks[task.id] = task
        self._prune_finished()
        if os.name == "nt":
            asyncio.create_task(self._pump_pipe(task, args, cwd, on_data, on_done))
        else:
            asyncio.create_task(
                self._pump_pty(task, args, cwd, on_data, on_done, line_mode)
            )
        return task

    async def _pump_pty(
        self,
        task: CliTask,
        args: list[str],
        cwd: Optional[str],
        on_data: BytesCallback,
        on_done: Optional[DoneCallback],
        line_mode: bool = False,
    ) -> None:
        import fcntl
        import pty
        import struct
        import termios

        master, slave = pty.openpty()
        try:
            winsize = struct.pack("HHHH", 24, 80, 0, 0)
            fcntl.ioctl(master, termios.TIOCSWINSZ, winsize)
            task._master_fd = master
            task._proc = await asyncio.create_subprocess_exec(
                *args, cwd=cwd, env=self._env,
                stdin=slave, stdout=slave, stderr=slave,
                start_new_session=True,
            )
            os.close(slave)
            await self._read_master(task, master, on_data, line_mode)
            task.returncode = await task._proc.wait() if task._proc else 0
        except Exception as e:
            self._fail(task, e)
        finally:
            try:
                os.close(master)
            except OSError:
                pass
            task._master_fd = None
            await self._finish(task, on_done)

    async def _pump_pipe(
        self,
        task: CliTask,
        args: list[str],
        cwd: Optional[str],
        on_data: BytesCallback,
        on_done: Optional[DoneCallback],
    ) -> None:
        try:
            task._proc = await asyncio.create_subprocess_exec(
                *args, cwd=cwd, env=self._env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
            assert task._proc.stdout is not None
            async for raw in task._proc.stdout:
                await on_data(task, raw)
            task.returncode = await task._proc.wait()
        except Exception as e:
            self._fail(task, e)
        finally:
            await self._finish(task, on_done)

    def _fail(self, task: CliTask, e: Exception) -> None:
        task.error = str(e)
        if task.returncode is None:
            task.returncode = -1

    async def _finish(self, task: CliTask, on_done: Optional[DoneCallback]) -> None:
        task.finished_at = time.time()
        if task.status == "running":
            task.status = "done" if task.returncode == 0 else "error"
        if on_done:
            await on_done(task)

    async def _read_master(
        self,
        task: CliTask,
        master: int,
        on_data: BytesCallback,
        line_mode: bool = False,
    ) -> None:
        loop = asyncio.get_event_loop()
        buffer = b""
        line_sep = re.compile(rb"[\r\n]+")
        while True:
            try:
                chunk = await loop.run_in_executor(None, os.read, master, 4096)
            except OSError:
                break
            if not chunk:
                break
            if not line_mode:
                await on_data(task, chunk)
                continue
            buffer += chunk
            while True:
                # A trailing \r may be the first half of \r\n split across frames.
                if buffer.endswith(b"\r"):
                    break
                m = line_sep.search(buffer)
                if not m:
                    break
                line = buffer[:m.start()]
                buffer = buffer[m.end():]
                if line:
                    await on_data(task, line + b"\r\n")
                else:
                    await on_data(task, b"\r\n")
        if line_mode and buffer:
            await on_data(task, buffer)

    async def cancel(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task or task.status != "running" or task._proc is None:
            return False
        task.status = "cancelled"
        proc = task._proc
        if os.name == "nt":
            proc.terminate()
            return True
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            return True
        asyncio.create_task(self._kill_after_grace(proc))
        return True

    async def _kill_after_grace(self, proc: asyncio.subprocess.Process) -> None:
        try:
            await asyncio.wait_for(proc.wait(), timeout=CANCEL_GRACE_SECONDS)
        except asyncio.TimeoutError:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass

    def get_task(self, task_id: str) -> Optional[CliTask]:
        return self.tasks.get(task_id)

    def active_tasks(self) -> list[CliTask]:
        return [t for t in self.tasks.values() if t.status == "running"]

    def recent_tasks(self) -> list[CliTask]:
        return sorted(self.tasks.values(), key=lambda t: t.started_at, reverse=True)

    def _prune_finished(self) -> None:
        finished = [t for t in self.tasks.values() if t.status != "running"]
        if len(finished) <= FINISHED_TASKS_KEPT:
            return
        finished.sort(key=lambda t: t.started_at)
        for task in finished[: len(finished) - FINISHED_TASKS_KEPT]:
            del self.tasks[task.id]
