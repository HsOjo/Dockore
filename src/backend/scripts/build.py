#!/usr/bin/env python3
"""Build the Dockore backend as a PyInstaller onedir bundle for desktop embedding."""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_target_triple() -> str:
    """Return the Rust target triple for the current platform."""
    try:
        out = subprocess.check_output(["rustc", "--print", "host-tuple"], text=True).strip()
        if out:
            return out
    except Exception:
        pass

    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "aarch64" if machine == "arm64" else machine
    if system == "darwin":
        return f"{arch}-apple-darwin"
    if system == "windows":
        return f"{arch}-pc-windows-msvc"
    if system == "linux":
        return f"{arch}-unknown-linux-gnu"
    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def get_icon_path(frontend_dir: Path) -> Path:
    """Return the platform-specific icon path from the Tauri assets."""
    icons_dir = frontend_dir / "src-tauri" / "icons"
    system = platform.system().lower()
    if system == "darwin":
        return icons_dir / "icon.icns"
    return icons_dir / "icon.ico"


def write_spec(backend_dir: Path, spec_path: Path, icon_path: Path) -> None:
    """Generate a PyInstaller spec file for onedir bundling."""
    entry = backend_dir / "app" / "main.py"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    version_file = backend_dir.parent.parent / "VERSION"
    datas = [(str(version_file), ".")]

    spec = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    [{entry.as_posix()!r}],
    pathex=[{backend_dir.as_posix()!r}],
    binaries=[],
    datas={datas!r},
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.supervisors",
        "fastapi",
        "fastapi.dependencies",
        "sqlalchemy.dialects.sqlite",
        "aiosqlite",
        "itsdangerous",
        "app",
        "app.api",
        "app.core",
        "app.models",
        "app.schemas",
        "app.services",
        "websockets",
        "httptools",
        "watchfiles",
        "uvloop",
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=["tkinter", "_tkinter", "matplotlib"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="dockore-backend",
    icon={icon_path.as_posix()!r},
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="backend",
)
'''
    spec_path.write_text(spec, encoding="utf-8")


def main() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    project_root = backend_dir.parent.parent
    frontend_dir = project_root / "src" / "frontend"
    binaries_dir = frontend_dir / "src-tauri" / "binaries"
    spec_path = backend_dir / "scripts" / "backend-sidecar.spec"
    pyinstaller_out = binaries_dir / "backend"
    backend_dist = binaries_dir / "backend-dist"
    icon_path = get_icon_path(frontend_dir)
    target_triple = get_target_triple()

    print(f"Target triple: {target_triple}")
    print(f"Backend entry: {backend_dir / 'app' / 'main.py'}")
    print(f"Output dir: {backend_dist}")
    print(f"Icon: {icon_path}")

    if not icon_path.exists():
        raise FileNotFoundError(f"Backend icon not found: {icon_path}")

    # Clean previous build artifacts.
    if pyinstaller_out.exists():
        shutil.rmtree(pyinstaller_out)
    if backend_dist.exists():
        shutil.rmtree(backend_dist)

    build_dir = backend_dir / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    binaries_dir.mkdir(parents=True, exist_ok=True)

    # Generate the PyInstaller spec.
    write_spec(backend_dir, spec_path, icon_path)

    # Run PyInstaller in onedir mode.
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(spec_path),
        "--noconfirm",
        "--clean",
        "--distpath",
        str(binaries_dir),
        "--workpath",
        str(build_dir),
    ]
    print("Running:", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, cwd=backend_dir)

    if not pyinstaller_out.exists():
        raise RuntimeError("PyInstaller did not create output directory")

    # PyInstaller names the output directory "backend"; rename for clarity.
    pyinstaller_out.rename(backend_dist)

    print(f"Built backend bundle: {backend_dist}")


if __name__ == "__main__":
    main()
