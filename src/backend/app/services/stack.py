from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Optional

from app.models import StackRegistration
from app.services.cli import Docker
from app.services.git import COMPOSE_FILE_NAMES

STACK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def derive_status(containers: list[dict]) -> str:
    running = sum(1 for c in containers if c["state"] == "running")
    total = len(containers)
    if total == 0:
        return "inactive"
    if running == total:
        return "running"
    if running == 0:
        return "stopped"
    return "partial"


class StackService:
    """Merge label discovery with the registry, deriving status and the
    file-accessibility matrix.

    Discovery intentionally stays on the single SDK label scan: it is the only
    source that yields container details in one call, and keeps one discovery
    implementation instead of parallel CLI/SDK paths. The compose CLI owns
    operations (lifecycle/up/pull/logs/config), not discovery.
    """

    def __init__(self, docker: Docker, stacks_dir: str = ""):
        self._docker = docker
        self._stacks_dir = stacks_dir

    @property
    def container_mode(self) -> bool:
        """DOCKORE_STACKS_DIR set (baked into the Docker image) => container deploy."""
        return bool(self._stacks_dir)

    @property
    def stacks_dir(self) -> str:
        return self._stacks_dir

    def file_accessible(self, config_files: list[str], registered: bool) -> bool:
        if not config_files:
            return False
        if self.container_mode:
            return self._under_stacks_dir(config_files)
        return registered

    def check_file_allowed(self, config_files: list[str], registered: bool) -> None:
        if not self.file_accessible(config_files, registered):
            raise PermissionError("stack files are not accessible for this stack")

    def _under_stacks_dir(self, paths: list[str]) -> bool:
        try:
            root = Path(self._stacks_dir).resolve()
        except OSError:
            return False
        return all(self._is_under(root, Path(p)) for p in paths)

    @staticmethod
    def _absolutize(working_dir: str, path: str) -> str:
        """Compose labels may carry config files relative to working_dir."""
        if not working_dir or Path(path).is_absolute():
            return path
        return str(Path(working_dir) / path)

    @staticmethod
    def _is_under(root: Path, path: Path) -> bool:
        try:
            path.resolve().relative_to(root)
            return True
        except (ValueError, OSError):
            return False

    async def list(self, registrations: list[StackRegistration]) -> list[dict]:
        discovered = await self._docker.stack.scan()
        reg_map = {r.name: r for r in registrations}
        items = []
        for name, data in discovered.items():
            reg = reg_map.pop(name, None)
            items.append(self._to_item(data, reg))
        for reg in reg_map.values():
            items.append(await self._registration_item(reg))
        items.sort(key=lambda i: i["name"])
        return items

    async def get(
        self, name: str, registrations: list[StackRegistration],
    ) -> Optional[dict]:
        items = await self.list(registrations)
        return next((i for i in items if i["name"] == name), None)

    def _to_item(self, data: dict, reg: Optional[StackRegistration]) -> dict:
        files_str = (
            reg.config_files
            if reg and reg.config_files
            else data["config_files"]
        )
        working_dir = reg.path if reg else data["working_dir"]
        config_files = [
            self._absolutize(working_dir, f)
            for f in files_str.split(",")
            if f
        ]
        containers = data["containers"]
        return dict(
            name=data["name"],
            status=derive_status(containers),
            running=sum(1 for c in containers if c["state"] == "running"),
            total=len(containers),
            containers=containers,
            working_dir=working_dir,
            config_files=config_files,
            registered=reg is not None,
            source=(reg.source if reg else "discovered"),
            file_accessible=self.file_accessible(config_files, reg is not None),
        )

    async def _registration_item(self, reg: StackRegistration) -> dict:
        config_files = [f for f in reg.config_files.split(",") if f]
        exists = await asyncio.to_thread(Path(reg.path).exists)
        return dict(
            name=reg.name,
            status="inactive" if exists else "missing",
            running=0,
            total=0,
            containers=[],
            working_dir=reg.path,
            config_files=config_files,
            registered=True,
            source=reg.source,
            file_accessible=exists and self.file_accessible(config_files, True),
        )

    def resolve_create_target(
        self, name: str, directory: Optional[str] = None,
    ) -> tuple[Path, Path]:
        """Target paths for a new stack: <base>/<name>/compose.yml."""
        if self.container_mode:
            base = Path(self._stacks_dir)
        elif directory:
            base = Path(directory)
        else:
            raise ValueError("directory is required when stacks_dir is not configured")
        stack_dir = base / name
        return stack_dir, stack_dir / "compose.yml"

    def resolve_register_target(self, path: str) -> tuple[Path, list[Path]]:
        """Validate a registration: dir must exist (and stay under stacks_dir
        in container mode) and hold at least one compose file."""
        stack_dir = Path(path).resolve()
        if self.container_mode:
            try:
                stack_dir.relative_to(Path(self._stacks_dir).resolve())
            except ValueError:
                raise ValueError("stack directory is outside stacks_dir")
        if not stack_dir.is_dir():
            raise ValueError(f"Directory not found: {path}")
        files = sorted(
            f for f in stack_dir.iterdir()
            if f.is_file() and f.name.lower() in COMPOSE_FILE_NAMES
        )
        if not files:
            raise ValueError(f"No compose file found in: {path}")
        return stack_dir, files
