import json
from typing import Any, Optional

from app.services.cli import CliExecutor, CliInfo, CliTask


def parse_json_output(text: str) -> list[dict[str, Any]]:
    """Compose --format json emits either a JSON array or NDJSON depending on version."""
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


class ComposeService:
    """docker compose subcommands over a detected CLI (v2 plugin or v1 binary)."""

    def __init__(self, cli: CliInfo, executor: CliExecutor):
        self._cli = cli
        self._exec = executor

    @property
    def cli(self) -> CliInfo:
        return self._cli

    @property
    def executor(self) -> CliExecutor:
        return self._exec

    def _args(
        self,
        *cmd: str,
        project: Optional[str] = None,
        files: Optional[list[str]] = None,
    ) -> list[str]:
        args = list(self._cli.command)
        for f in files or []:
            args += ["-f", f]
        if project:
            args += ["-p", project]
        args += cmd
        return args

    async def ls_json(self) -> list[dict[str, Any]]:
        if not self._cli.is_v2:
            return []
        out = await self._exec.run(self._args("ls", "-a", "--format", "json"))
        return parse_json_output(out)

    async def ps_json(self, project: str) -> list[dict[str, Any]]:
        if not self._cli.is_v2:
            return []
        out = await self._exec.run(
            self._args("ps", "-a", "--format", "json", project=project)
        )
        return parse_json_output(out)

    async def validate(self, files: list[str], cwd: str) -> None:
        """Raise CliError when the compose files are invalid."""
        await self._exec.run(self._args("config", "-q", files=files), cwd=cwd)

    async def config_json(
        self, project: str, files: list[str], cwd: str,
    ) -> dict[str, Any]:
        """Normalized, interpolated compose config (v2 only) as a dict."""
        out = await self._exec.run(
            self._args(
                "config", "--format", "json", project=project, files=files,
            ),
            cwd=cwd,
        )
        return json.loads(out)

    async def lifecycle(
        self, project: str, action: str, files: Optional[list[str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        """start/stop/restart work with just a project name (no compose file needed)."""
        await self._exec.run(self._args(action, project=project, files=files), cwd=cwd)

    async def down(
        self, project: str, remove_volumes: bool, on_data, on_done=None,
    ) -> CliTask:
        args = self._args("down", project=project)
        if remove_volumes:
            args.append("--volumes")
        return await self._exec.stream("down", project, args, on_data, on_done=on_done)

    async def pull(
        self, project: str, files: list[str], cwd: str, on_data, on_done=None,
    ) -> CliTask:
        args = self._args("pull", project=project, files=files)
        return await self._exec.stream("pull", project, args, on_data, cwd=cwd, on_done=on_done)

    async def up(
        self, project: str, files: list[str], cwd: str, on_data, on_done=None,
    ) -> CliTask:
        args = self._args("up", "-d", project=project, files=files)
        return await self._exec.stream("up", project, args, on_data, cwd=cwd, on_done=on_done)
    async def logs(
        self,
        project: str,
        on_data,
        files: Optional[list[str]] = None,
        cwd: Optional[str] = None,
        follow: bool = True,
        tail: str = "200",
        since: Optional[str] = None,
        until: Optional[str] = None,
        on_done=None,
    ):
        args = self._args("logs", "--no-color", "--tail", tail, project=project, files=files)
        if since:
            args += ["--since", since]
        if until:
            args += ["--until", until]
        if follow:
            args.append("-f")
        return await self._exec.stream(
            "logs", project, args, on_data, cwd=cwd, on_done=on_done, line_mode=True,
        )
