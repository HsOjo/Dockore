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
    def _scan_compose_files(stack_dir: Path) -> list[Path]:
        try:
            return sorted(
                f for f in stack_dir.iterdir()
                if f.is_file() and f.name.lower() in COMPOSE_FILE_NAMES
            )
        except OSError:
            return []

    @staticmethod
    def _files_exist(files: list[str]) -> bool:
        return bool(files) and all(Path(f).is_file() for f in files)

    def _can_inspect(self, paths: list[str]) -> bool:
        """Existence checks are only meaningful for reachable files; in
        container mode host paths outside stacks_dir cannot be inspected."""
        if not self.container_mode:
            return True
        return bool(paths) and self._under_stacks_dir(paths)

    def _resolve_files(
        self,
        reg: StackRegistration,
        working_dir: str,
        reg_files: list[str],
        discovered_files: list[str],
    ) -> list[str]:
        """Registered paths win, but self-heal when they vanished (rename/
        move of the compose file): fall back to discovery labels, then to a
        directory scan. Repairs are written back to the registration; the
        caller commits the session."""
        if not reg_files:
            return discovered_files
        if self._files_exist(reg_files):
            return reg_files
        if not self._can_inspect([working_dir, *reg_files]):
            return reg_files
        healed = discovered_files
        if not self._files_exist(healed):
            healed = (
                [str(f) for f in self._scan_compose_files(Path(working_dir))]
                if working_dir else []
            )
        if healed:
            reg.config_files = ",".join(healed)
            return healed
        return reg_files

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

    @staticmethod
    def _is_git_repo(working_dir: str) -> bool:
        return bool(working_dir) and (Path(working_dir) / ".git").is_dir()

    def _resolve_is_git_repo(
        self, stored: Optional[bool], working_dir: str,
    ) -> bool:
        if stored is not None:
            return stored
        return self._is_git_repo(working_dir)

    def _to_item(self, data: dict, reg: Optional[StackRegistration]) -> dict:
        discovered_files = [
            self._absolutize(data["working_dir"], f)
            for f in data["config_files"].split(",")
            if f
        ]
        if reg:
            working_dir = reg.path
            config_files = self._resolve_files(
                reg,
                working_dir,
                [
                    self._absolutize(working_dir, f)
                    for f in reg.config_files.split(",")
                    if f
                ],
                discovered_files,
            )
        else:
            working_dir = data["working_dir"]
            config_files = discovered_files
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
            is_git_repo=self._resolve_is_git_repo(
                reg.is_git_repo if reg else None, working_dir,
            ),
        )

    async def _registration_item(self, reg: StackRegistration) -> dict:
        exists = await asyncio.to_thread(Path(reg.path).exists)
        config_files = [f for f in reg.config_files.split(",") if f]
        if exists:
            config_files = self._resolve_files(reg, reg.path, config_files, [])
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
            is_git_repo=exists and self._resolve_is_git_repo(
                reg.is_git_repo, reg.path,
            ),
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
        files = self._scan_compose_files(stack_dir)
        if not files:
            raise ValueError(f"No compose file found in: {path}")
        return stack_dir, files
