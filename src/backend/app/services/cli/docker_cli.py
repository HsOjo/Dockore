import json
from typing import Optional

from .errors import DockerApiError, DockerError, DockerNotFound
from .executor import CliError, CliExecutor

_NOT_FOUND_MARKERS = (
    "no such container",
    "no such image",
    "no such network",
    "no such volume",
    "no such object",
    "not found",
)

_DAEMON_MARKERS = (
    "cannot connect to the docker daemon",
    "error during connect",
    "is the docker daemon running",
    "connection refused",
)


def map_cli_error(error: CliError) -> DockerError:
    output = (error.output or "").strip()
    lowered = output.lower()
    if any(m in lowered for m in _NOT_FOUND_MARKERS):
        return DockerNotFound(output)
    if any(m in lowered for m in _DAEMON_MARKERS):
        return DockerError(output)
    return DockerApiError(output)


class DockerCli:
    """Runs `docker` CLI commands for one docker_host and maps failures to DockerError."""

    def __init__(self, docker_host: str = ""):
        self.docker_host = docker_host
        self.executor = CliExecutor(docker_host)

    async def run(self, *args: str, cwd: Optional[str] = None) -> str:
        try:
            return await self.executor.run(["docker", *args], cwd=cwd)
        except CliError as e:
            raise map_cli_error(e) from e

    async def run_json_lines(self, *args: str) -> list[dict]:
        """Run a `--format '{{json .}}'` command and parse line-delimited JSON."""
        text = await self.run(*args)
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    async def inspect(self, *args: str) -> dict:
        """`docker inspect ...` returning the first object."""
        data = json.loads(await self.run("inspect", *args))
        if not data:
            raise DockerNotFound(f"inspect returned no object: {' '.join(args)}")
        return data[0]

    async def inspect_list(self, *args: str) -> list[dict]:
        return json.loads(await self.run("inspect", *args))
