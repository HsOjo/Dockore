import asyncio
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .env import augmented_path

_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


@dataclass
class CliInfo:
    """A detected compose CLI: command prefix, version and capability flags."""

    command: list[str]
    version: str
    major: int
    progress: bool
    binary: str

    @property
    def is_v2(self) -> bool:
        return self.major >= 2


async def _try_version(command: list[str], path: str) -> Optional[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *command, "version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={"PATH": path},
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
    except (OSError, asyncio.TimeoutError):
        return None
    if proc.returncode != 0:
        return None
    return out.decode(errors="ignore")


async def _supports_progress_option(command: list[str], path: str) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            *command, "up", "--help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={"PATH": path},
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
    except (OSError, asyncio.TimeoutError):
        return False
    return proc.returncode == 0 and b"--progress" in out


def _candidates(cli_path: str, path: str) -> list[list[str]]:
    if cli_path and cli_path != "auto":
        binary = str(Path(cli_path))
        if "docker-compose" in Path(cli_path).name:
            return [[binary], [binary, "compose"]]
        return [[binary, "compose"], [binary]]
    candidates = []
    docker = shutil.which("docker", path=path)
    if docker:
        candidates.append([docker, "compose"])
    legacy = shutil.which("docker-compose", path=path)
    if legacy:
        candidates.append([legacy])
    return candidates


async def detect_compose_cli(cli_path: str = "") -> Optional[CliInfo]:
    """Probe for a compose CLI: v2 plugin first, legacy v1 binary as fallback."""
    path = augmented_path()
    for command in _candidates(cli_path, path):
        output = await _try_version(command, path)
        if not output:
            continue
        match = _VERSION_RE.search(output)
        if not match:
            continue
        major = int(match.group(1))
        progress = major >= 2 and await _supports_progress_option(command, path)
        return CliInfo(
            command=command,
            version=match.group(0).lstrip("v"),
            major=major,
            progress=progress,
            binary=command[0],
        )
    return None
