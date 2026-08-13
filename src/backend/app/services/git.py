import os
import shutil
from pathlib import Path
from typing import Optional

from app.core.validators import validate_no_dash
from app.services.cli import CliError, CliExecutor, CliTask, augmented_path

COMPOSE_FILE_NAMES = frozenset({
    "compose.yml",
    "compose.yaml",
    "docker-compose.yml",
    "docker-compose.yaml",
})
ENV_TEMPLATE_NAMES = frozenset({
    ".env.example",
    ".env.sample",
    ".env.template",
    "example.env",
    "sample.env",
    "template.env",
})
ENV_TEMPLATE_SUFFIXES = (".env.example", ".env.sample", ".env.template")
SKIP_DIRS = frozenset({".git", "node_modules"})


def git_available() -> bool:
    return shutil.which("git", path=augmented_path()) is not None


async def detect_git_repo(executor: CliExecutor, path: Path) -> Optional[bool]:
    """Whether path sits inside a git work tree (subdir-aware via rev-parse).

    None when git CLI is missing, so callers can defer to a runtime check.
    """
    if not git_available():
        return None
    try:
        await executor.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
        )
        return True
    except CliError:
        return False


async def clone_stream(
    executor: CliExecutor,
    url: str,
    branch: Optional[str],
    target: Path,
    on_data,
    on_done=None,
) -> CliTask:
    url = validate_no_dash(url, "git url")
    if branch:
        branch = validate_no_dash(branch, "branch")
    args = ["git", "clone", "--progress"]
    if branch:
        args += ["--branch", branch]
    args += [url, str(target)]
    return await executor.stream("clone", target.name, args, on_data, on_done=on_done)


async def pull_stream(
    executor: CliExecutor,
    workdir: Path,
    on_data,
    on_done=None,
) -> CliTask:
    args = ["git", "-C", str(workdir), "pull", "--progress"]
    return await executor.stream("pull-repo", workdir.name, args, on_data, on_done=on_done)


def _is_env_template(name: str) -> bool:
    lower = name.lower()
    return lower in ENV_TEMPLATE_NAMES or lower.endswith(ENV_TEMPLATE_SUFFIXES)


def scan_candidates(repo_dir: Path) -> tuple[list[str], list[str]]:
    """Repo-relative paths of compose files and .env templates, at any depth."""
    composes, env_templates = [], []
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            rel = (Path(root) / f).relative_to(repo_dir).as_posix()
            if f.lower() in COMPOSE_FILE_NAMES:
                composes.append(rel)
            elif _is_env_template(f):
                env_templates.append(rel)
    return sorted(composes), sorted(env_templates)


def resolve_in_repo(repo_dir: Path, rel: str) -> Path:
    """Resolve a repo-relative path, rejecting traversal outside the repo."""
    root = repo_dir.resolve()
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError(f"Path escapes repository: {rel}")
    return path
