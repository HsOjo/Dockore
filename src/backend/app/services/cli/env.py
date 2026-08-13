import os
import sys
from pathlib import Path
from typing import Optional

from app.core.settings_service import ProxyConfig

EXTRA_BIN_DIRS = {
    "darwin": ["/usr/local/bin", "/opt/homebrew/bin", "/usr/bin"],
    "win32": [
        r"C:\Program Files\Docker\Docker\resources\bin",
        r"C:\Program Files\Docker\cli-plugins",
    ],
    "linux": ["/usr/local/bin", "/usr/bin", "/snap/bin"],
}


def augmented_path() -> str:
    """PATH with common docker install locations appended.

    Packaged desktop apps (e.g. launched from a Tauri bundle) inherit a minimal
    PATH that often misses the docker CLI.
    """
    parts = os.environ.get("PATH", "").split(os.pathsep)
    seen = {p for p in parts if p}
    for d in EXTRA_BIN_DIRS.get(sys.platform, EXTRA_BIN_DIRS["linux"]):
        if d not in seen:
            parts.append(d)
            seen.add(d)
    home_docker = str(Path.home() / ".docker" / "bin")
    if home_docker not in seen:
        parts.append(home_docker)
    return os.pathsep.join(p for p in parts if p)


def build_env(docker_host: str, proxy: Optional[ProxyConfig] = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = augmented_path()
    if docker_host:
        env["DOCKER_HOST"] = docker_host
    if proxy:
        proxy.apply(env)
    return env
