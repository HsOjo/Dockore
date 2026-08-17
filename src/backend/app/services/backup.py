from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.config import settings
from app.services.cli import Docker

HELPER_IMAGE = "alpine:latest"
MANIFEST_NAME = "manifest.json"
BACKUP_ID_RE = re.compile(r"^[0-9]{8}-[0-9]{6}(-[0-9]+)?$")
VALID_KEY_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")

VIRTUAL_FS_TYPES = (
    "proc", "sysfs", "devtmpfs", "devpts", "tmpfs", "cgroup", "cgroup2",
    "mqueue", "shm", "nsfs", "pstore", "bpf", "tracefs", "debugfs",
    "securityfs", "hugetlbfs", "fusectl", "configfs", "ramfs", "autofs",
    "binfmt_misc",
)


@dataclass
class VolumeMount:
    key: str
    name: str


@dataclass
class BindMount:
    source: str
    name: str = ""

    @property
    def archive_name(self) -> str:
        return self.name or self.source.rstrip("/").rsplit("/", 1)[-1] or "root"


@dataclass
class MountPlan:
    volumes: list[VolumeMount] = field(default_factory=list)
    binds: list[BindMount] = field(default_factory=list)


@dataclass
class EnvFileRef:
    path: str
    required: bool = True


def parse_mounts(config: dict[str, Any], project: str) -> MountPlan:
    """Split normalized compose config into named volumes and bind mounts.

    Anonymous volumes (no source) and tmpfs/npipe mounts are skipped: only
    explicitly declared persistent storage is backed up.
    """
    vol_names = {}
    for key, spec in (config.get("volumes") or {}).items():
        vol_names[key] = (spec or {}).get("name") or f"{project}_{key}"
    plan = MountPlan()
    seen_volumes: set[str] = set()
    seen_binds: set[str] = set()
    used_names: set[str] = set()
    for svc in (config.get("services") or {}).values():
        for mount in (svc or {}).get("volumes") or []:
            mtype = mount.get("type")
            source = mount.get("source") or ""
            if mtype == "volume":
                if not source:
                    continue
                if not VALID_KEY_RE.match(source):
                    raise ValueError(f"unsupported volume key: {source!r}")
                name = vol_names.get(source, f"{project}_{source}")
                if name not in seen_volumes:
                    seen_volumes.add(name)
                    plan.volumes.append(VolumeMount(key=source, name=name))
            elif mtype == "bind":
                if source and source not in seen_binds:
                    seen_binds.add(source)
                    base = source.rstrip("/").rsplit("/", 1)[-1] or "root"
                    name, n = base, 1
                    while name in used_names:
                        n += 1
                        name = f"{base}-{n}"
                    used_names.add(name)
                    plan.binds.append(BindMount(source=source, name=name))
    return plan


def extract_env_files(config_files: list[str]) -> list[EnvFileRef]:
    """env_file references from the raw compose files; `config --format json`
    merges them into `environment` and loses the file paths, hence pyyaml."""
    refs: list[EnvFileRef] = []
    seen: set[str] = set()
    for compose_file in config_files:
        data = yaml.safe_load(Path(compose_file).read_text()) or {}
        base = Path(compose_file).parent
        for svc in (data.get("services") or {}).values():
            entries = (svc or {}).get("env_file") or []
            if isinstance(entries, (str, dict)):
                entries = [entries]
            for entry in entries:
                if isinstance(entry, str):
                    path, required = entry, True
                else:
                    path = entry.get("path") or ""
                    required = bool(entry.get("required", True))
                if not path:
                    continue
                resolved = Path(path)
                if not resolved.is_absolute():
                    resolved = base / resolved
                key = str(resolved)
                if key not in seen:
                    seen.add(key)
                    refs.append(EnvFileRef(path=key, required=required))
    return refs


class BackupService:
    """Filesystem layout and helper-container plumbing for stack backups.

    Backup root: DOCKORE_BACKUPS_DIR when set, else <data_dir>/backups in
    desktop mode. In container mode the variable is required (and must be
    bind-mounted at an identical host path) because the helper container
    mounts the backup directory through the docker daemon.
    """

    def __init__(self, container_mode: bool, docker: Optional[Docker] = None):
        self._container_mode = container_mode
        self._docker = docker

    @property
    def root(self) -> Optional[Path]:
        if settings.dockore_backups_dir:
            return Path(settings.dockore_backups_dir)
        if self._container_mode:
            return None
        return settings.data_dir / "backups"

    def stack_dir(self, stack: str) -> Path:
        root = self.root
        if root is None:
            raise RuntimeError("backups are not configured")
        return root / stack

    def new_backup_dir(self, stack: str) -> tuple[str, Path]:
        base = self.stack_dir(stack)
        base.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_id = stamp
        n = 1
        while (base / backup_id).exists():
            n += 1
            backup_id = f"{stamp}-{n}"
        backup_dir = base / backup_id
        (backup_dir / "volumes").mkdir(parents=True)
        (backup_dir / "binds").mkdir()
        (backup_dir / "files").mkdir()
        return backup_id, backup_dir

    def resolve(self, stack: str, backup_id: str) -> Path:
        if not BACKUP_ID_RE.match(backup_id):
            raise ValueError(f"invalid backup id: {backup_id!r}")
        backup_dir = self.stack_dir(stack) / backup_id
        if not backup_dir.is_dir() or not (backup_dir / MANIFEST_NAME).is_file():
            raise KeyError(backup_id)
        return backup_dir

    async def filter_existing_volumes(
        self, plan: MountPlan, skipped: list[dict],
    ) -> MountPlan:
        """Drop volumes the daemon does not have (never-created stacks) into
        `skipped` instead of letting docker auto-create empty volumes."""
        if self._docker is None:
            return plan
        kept = []
        for vol in plan.volumes:
            if await self._docker.volume.item(vol.name) is not None:
                kept.append(vol)
            else:
                skipped.append({
                    "type": "volume",
                    "ref": vol.name,
                    "reason": "volume not found",
                })
        return MountPlan(volumes=kept, binds=plan.binds)

    def stage_env_files(
        self, refs: list[EnvFileRef], skipped: list[dict],
    ) -> list[Path]:
        """Validate env_file refs; unreadable required refs abort the backup."""
        existing = []
        for ref in refs:
            path = Path(ref.path)
            if path.is_file():
                existing.append(path)
            elif not ref.required:
                skipped.append({
                    "type": "env_file",
                    "ref": ref.path,
                    "reason": "file not found (required: false)",
                })
            else:
                raise ValueError(f"env_file not found: {ref.path}")
        return existing

    async def stage_files(
        self,
        backup_dir: Path,
        config_files: list[str],
        env_path: Optional[Path],
        env_files: list[Path],
    ) -> list[dict]:
        """Copy compose and env files into files/, recording manifest entries."""

        def _copy_all() -> list[dict]:
            entries = []
            used: set[str] = set()

            def store(source: Path, kind: str) -> None:
                name = source.name
                if name in used:
                    name = f"{len(used)}-{source.name}"
                used.add(name)
                shutil.copy2(source, backup_dir / "files" / name)
                entries.append({"kind": kind, "source": str(source), "stored": name})

            for f in config_files:
                store(Path(f), "compose")
            if env_path is not None and env_path.is_file():
                store(env_path, "env")
            for f in env_files:
                store(f, "env_file")
            return entries

        return await asyncio.to_thread(_copy_all)

    def helper_script(self, plan: MountPlan) -> str:
        """One tar per mount; a failing tar degrades to a warning recorded in
        warnings.txt (busybox tar has no --ignore-failed-read) instead of
        aborting the whole backup. Binds whose mount is a virtual filesystem
        (/proc, /sys, /dev, tmpfs, ...) carry no persistent data and are
        skipped into skipped.txt, detected via /proc/mounts in the helper."""
        lines = ["set -e"]
        for vol in plan.volumes:
            key = shlex.quote(vol.key)
            name = shlex.quote(vol.name)
            begin = shlex.quote(f">>> volume {vol.name}")
            done = shlex.quote(f"<<< volume {vol.name}")
            lines.append(
                f"echo {begin}\n"
                f"tar --numeric-owner -cvzf /backup/volumes/{key}.tar.gz"
                f" -C /volumes/{key} ."
                f" && echo {done}"
                f" || printf 'volume\\t%s\\n' {name} >> /backup/warnings.txt"
            )
        virtual = "|".join(VIRTUAL_FS_TYPES)
        for i, bind in enumerate(plan.binds):
            src = shlex.quote(bind.source)
            archive = shlex.quote(bind.archive_name)
            begin = shlex.quote(f">>> bind {bind.source}")
            done = shlex.quote(f"<<< bind {bind.source}")
            skip = shlex.quote(f"--- bind {bind.source} skipped")
            lines.append(
                f"fstype=$(awk '$2 == \"/binds/bind-{i}\" "
                f"{{ print $3 }}' /proc/mounts)\n"
                f"case \"$fstype\" in\n"
                f"  {virtual}) echo {skip}"
                f" && printf 'bind\\t%s\\t%s\\n' {src} \"$fstype\""
                f" >> /backup/skipped.txt ;;\n"
                f"  *) echo {begin}\n"
                f"     if [ -d /binds/bind-{i} ]; then"
                f" tar --numeric-owner -cvzf /backup/binds/{archive}.tar.gz"
                f" -C /binds/bind-{i} .;"
                f" else tar --numeric-owner -cvzf /backup/binds/{archive}.tar.gz"
                f" -C /binds bind-{i}; fi"
                f" && echo {done}"
                f" || printf 'bind\\t%s\\n' {src} >> /backup/warnings.txt ;;\n"
                f"esac"
            )
        return "\n".join(lines)

    def helper_args(
        self, plan: MountPlan, backup_dir: Path, stack: str, backup_id: str,
    ) -> list[str]:
        """`-v` (not --mount) so a missing bind source is auto-created by the
        daemon, matching `compose up` semantics."""
        args = [
            "docker", "run", "--rm",
            "--name", f"dockore-backup-{stack}-{backup_id}",
        ]
        for vol in plan.volumes:
            args += ["-v", f"{vol.name}:/volumes/{vol.key}:ro"]
        for i, bind in enumerate(plan.binds):
            args += ["-v", f"{bind.source}:/binds/bind-{i}:ro"]
        args += ["-v", f"{backup_dir}:/backup"]
        args += [HELPER_IMAGE, "sh", "-c", self.helper_script(plan)]
        return args

    async def finalize(
        self,
        backup_dir: Path,
        backup_id: str,
        stack: str,
        was_running: bool,
        plan: MountPlan,
        files: list[dict],
        skipped: list[dict],
    ) -> None:
        """Write manifest.json with archive sizes after a successful run,
        merging the helper's warnings/skipped reports."""

        def _size(path: Path) -> int:
            try:
                return path.stat().st_size
            except OSError:
                return 0

        def _write() -> None:
            virtual = backup_dir / "skipped.txt"
            if virtual.is_file():
                for line in virtual.read_text().splitlines():
                    parts = line.split("\t")
                    if len(parts) == 3:
                        skipped.append({
                            "type": parts[0],
                            "ref": parts[1],
                            "reason": f"virtual filesystem ({parts[2]})",
                        })
            warnings = backup_dir / "warnings.txt"
            if warnings.is_file():
                for line in warnings.read_text().splitlines():
                    wtype, _, ref = line.partition("\t")
                    if ref:
                        skipped.append({
                            "type": wtype,
                            "ref": ref,
                            "reason": "archive may be incomplete (read errors)",
                        })
            skipped_refs = {(s["type"], s["ref"]) for s in skipped}
            volumes = []
            for vol in plan.volumes:
                if ("volume", vol.name) in skipped_refs:
                    continue
                archive = f"volumes/{vol.key}.tar.gz"
                volumes.append({
                    "key": vol.key,
                    "name": vol.name,
                    "archive": archive,
                    "size": _size(backup_dir / archive),
                })
            binds = []
            for bind in plan.binds:
                if ("bind", bind.source) in skipped_refs:
                    continue
                archive = f"binds/{bind.archive_name}.tar.gz"
                binds.append({
                    "source": bind.source,
                    "archive": archive,
                    "size": _size(backup_dir / archive),
                })
            created_at = datetime.strptime(
                backup_id[:15], "%Y%m%d-%H%M%S",
            ).replace(tzinfo=timezone.utc).isoformat()
            manifest = {
                "version": 1,
                "id": backup_id,
                "stack": stack,
                "created_at": created_at,
                "was_running": was_running,
                "files": files,
                "volumes": volumes,
                "binds": binds,
                "skipped": skipped,
            }
            (backup_dir / MANIFEST_NAME).write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False)
            )

        await asyncio.to_thread(_write)

    def list(self, stack: str) -> list[dict]:
        base = self.stack_dir(stack)
        if not base.is_dir():
            return []
        items = []
        for entry in base.iterdir():
            manifest_path = entry / MANIFEST_NAME
            if not entry.is_dir() or not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            size = sum(
                f.stat().st_size for f in entry.rglob("*") if f.is_file()
            )
            skipped = manifest.get("skipped", [])
            skipped_refs = {(s.get("type"), s.get("ref")) for s in skipped}
            items.append({
                "id": manifest.get("id", entry.name),
                "created_at": manifest.get("created_at", ""),
                "was_running": bool(manifest.get("was_running")),
                "size": size,
                "compose_files": [
                    f["stored"] for f in manifest.get("files", [])
                    if f.get("kind") == "compose"
                ],
                "env_files": [
                    f["stored"] for f in manifest.get("files", [])
                    if f.get("kind") in ("env", "env_file")
                ],
                "volumes": [
                    v for v in manifest.get("volumes", [])
                    if ("volume", v.get("name")) not in skipped_refs
                ],
                "binds": [
                    b for b in manifest.get("binds", [])
                    if ("bind", b.get("source")) not in skipped_refs
                ],
                "skipped": skipped,
            })
        items.sort(key=lambda i: i["id"], reverse=True)
        return items

    async def delete(self, stack: str, backup_id: str) -> None:
        backup_dir = self.resolve(stack, backup_id)
        await asyncio.to_thread(shutil.rmtree, backup_dir)

    async def cleanup(self, backup_dir: Path) -> None:
        await asyncio.to_thread(shutil.rmtree, backup_dir, ignore_errors=True)

    async def pack(self, stack: str, backup_id: str) -> Path:
        """Tar.gz the whole backup directory for download, rooted at
        <stack>-<backup_id> to match the downloaded file name."""
        backup_dir = self.resolve(stack, backup_id)

        def _pack() -> Path:
            fd, tmp = tempfile.mkstemp(
                prefix="dockore-backup-", suffix=".tar.gz",
            )
            os.close(fd)
            tmp_path = Path(tmp)
            with tarfile.open(tmp_path, "w:gz") as tar:
                tar.add(backup_dir, arcname=f"{stack}-{backup_id}")
            return tmp_path

        return await asyncio.to_thread(_pack)
