from typing import Any

from .docker_cli import DockerCli

LABEL_PROJECT = "com.docker.compose.project"
LABEL_WORKING_DIR = "com.docker.compose.project.working_dir"
LABEL_CONFIG_FILES = "com.docker.compose.project.config_files"
LABEL_SERVICE = "com.docker.compose.service"


def parse_labels(raw: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    key = ""
    for part in raw.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            labels[key] = value
        elif key:
            labels[key] += "," + part
    return labels


class StackDiscovery:
    """Group containers by compose project labels via `docker ps`."""

    def __init__(self, cli: DockerCli):
        self._cli = cli

    async def scan(self) -> dict[str, dict[str, Any]]:
        rows = await self._cli.run_json_lines(
            "ps", "-a", "--no-trunc", "--format", "{{json .}}",
        )
        stacks: dict[str, dict[str, Any]] = {}
        for row in rows:
            labels = parse_labels(row.get("Labels") or "")
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
                "id": row.get("ID", "")[:12],
                "name": (row.get("Names") or "").split(",")[0],
                "service": labels.get(LABEL_SERVICE, ""),
                "state": row.get("State", ""),
                "status": row.get("Status", ""),
            })
            if not entry["working_dir"]:
                entry["working_dir"] = labels.get(LABEL_WORKING_DIR, "")
                entry["config_files"] = labels.get(LABEL_CONFIG_FILES, "")
        return stacks
