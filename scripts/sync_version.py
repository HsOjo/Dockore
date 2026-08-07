#!/usr/bin/env python3
"""Sync the single VERSION source to files that must contain a static version."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "VERSION"
CARGO_TOML = ROOT / "src" / "frontend" / "src-tauri" / "Cargo.toml"
PYPROJECT_TOML = ROOT / "src" / "backend" / "pyproject.toml"
UV_LOCK = ROOT / "src" / "backend" / "uv.lock"
BACKEND_DIR = ROOT / "src" / "backend"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def set_version(version: str) -> None:
    if not VERSION_RE.match(version):
        raise SystemExit(f"Invalid version: {version!r}")
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")


def replace_version(text: str, version: str) -> str:
    new_text, count = re.subn(
        r'^version = "[^"]+"',
        f'version = "{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise SystemExit("Could not find version line to update")
    return new_text


def update_cargo_toml(version: str, dry_run: bool) -> None:
    text = CARGO_TOML.read_text(encoding="utf-8")
    new_text = replace_version(text, version)
    if dry_run:
        print(f"Would update {CARGO_TOML}")
    else:
        CARGO_TOML.write_text(new_text, encoding="utf-8")


def update_pyproject_toml(version: str, dry_run: bool) -> None:
    text = PYPROJECT_TOML.read_text(encoding="utf-8")
    new_text = replace_version(text, version)
    if dry_run:
        print(f"Would update {PYPROJECT_TOML}")
    else:
        PYPROJECT_TOML.write_text(new_text, encoding="utf-8")


def run_uv_lock(dry_run: bool) -> None:
    if dry_run:
        print(f"Would run uv lock in {BACKEND_DIR}")
        return
    subprocess.run(["uv", "lock"], cwd=BACKEND_DIR, check=True)


def get_locked_version() -> str | None:
    lock = tomllib.load(UV_LOCK.open("rb"))
    for package in lock.get("package", []):
        if package.get("name") == "dockore-backend":
            return package.get("version")
    return None


def check() -> None:
    version = read_version()
    errors: list[str] = []

    # Cargo.toml
    cargo_text = CARGO_TOML.read_text(encoding="utf-8")
    m = re.search(r'^version = "([^"]+)"', cargo_text, re.MULTILINE)
    if not m:
        errors.append(f"{CARGO_TOML}: missing version")
    elif m.group(1) != version:
        errors.append(f"{CARGO_TOML}: expected {version}, got {m.group(1)}")

    # pyproject.toml
    pyproject = tomllib.load(PYPROJECT_TOML.open("rb"))
    project_version = pyproject.get("project", {}).get("version")
    if project_version != version:
        errors.append(f"{PYPROJECT_TOML}: expected {version}, got {project_version}")

    # uv.lock
    locked_version = get_locked_version()
    if locked_version is None:
        errors.append(f"{UV_LOCK}: missing dockore-backend package")
    elif locked_version != version:
        errors.append(f"{UV_LOCK}: expected {version}, got {locked_version}")

    if errors:
        print("Version mismatch:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("All versions are in sync.")


def sync(version: str | None, dry_run: bool) -> None:
    if version is None:
        version = read_version()
    else:
        if not VERSION_RE.match(version):
            raise SystemExit(f"Invalid version: {version!r}")
        if dry_run:
            print(f"Would set VERSION to {version}")
        else:
            set_version(version)

    update_cargo_toml(version, dry_run)
    update_pyproject_toml(version, dry_run)
    run_uv_lock(dry_run)

    if dry_run:
        print(f"Dry-run complete for version {version}")
    else:
        print(f"Synced version {version}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync version from VERSION file")
    parser.add_argument("version", nargs="?", help="Target version, e.g. 0.3.0")
    parser.add_argument("--check", action="store_true", help="Check if all files are in sync")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    if args.check and args.dry_run:
        raise SystemExit("--check and --dry-run are mutually exclusive")

    if args.check:
        check()
    else:
        sync(args.version, args.dry_run)


if __name__ == "__main__":
    main()
