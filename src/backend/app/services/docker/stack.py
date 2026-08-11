import asyncio
from typing import Any

LABEL_PROJECT = "com.docker.compose.project"
LABEL_WORKING_DIR = "com.docker.compose.project.working_dir"
LABEL_CONFIG_FILES = "com.docker.compose.project.config_files"
LABEL_SERVICE = "com.docker.compose.service"


class StackDiscovery:
    """Group containers by compose project labels.

    This is the fallback discovery path when no compose CLI is available (or
    only a v1 binary, which lacks --format json); it also works without a CLI
    for read-only listing.
    """

    def __init__(self, api):
        self._api = api

    async def scan(self) -> dict[str, dict[str, Any]]:
        containers = await asyncio.to_thread(self._api.containers, all=True)
        stacks: dict[str, dict[str, Any]] = {}
        for c in containers:
            labels = c.get("Labels") or {}
            name = labels.get(LABEL_PROJECT)
            if not name:
                continue
            entry = stacks.setdefault(name, {
                "name": name,
                "working_dir": labels.get(LABEL_WORKING_DIR, ""),
                "config_files": labels.get(LABEL_CONFIG_FILES, ""),
                "containers": [],
            })
            entry["containers"].append({
                "id": c.get("Id", "")[:12],
                "name": (c.get("Names") or [""])[0].lstrip("/"),
                "service": labels.get(LABEL_SERVICE, ""),
                "state": c.get("State", ""),
                "status": c.get("Status", ""),
            })
            if not entry["working_dir"]:
                entry["working_dir"] = labels.get(LABEL_WORKING_DIR, "")
                entry["config_files"] = labels.get(LABEL_CONFIG_FILES, "")
        return stacks
