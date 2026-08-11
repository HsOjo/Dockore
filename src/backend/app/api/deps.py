from dataclasses import dataclass
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings_service
from app.core.config import settings
from app.core.database import get_db
from app.services.cli import CliInfo, detect_compose_cli
from app.services.compose import ComposeService, stack_tasks
from app.services.docker.client import Docker, get_client
from app.services.stack import StackService


async def resolve_docker(session: AsyncSession) -> Docker:
    """Build the Docker facade from the effective docker_host setting."""
    all_settings = await settings_service.get_all(session)
    return Docker(get_client(all_settings["docker_host"]))


async def get_docker(session: AsyncSession = Depends(get_db)) -> Docker:
    return await resolve_docker(session)


_cli_cache: dict[str, Optional[CliInfo]] = {}


async def get_cli_info(cli_path: str) -> Optional[CliInfo]:
    """Cached compose CLI detection; a changed setting triggers a re-probe."""
    if cli_path not in _cli_cache:
        _cli_cache[cli_path] = await detect_compose_cli(cli_path)
    return _cli_cache[cli_path]


@dataclass
class StackContext:
    stack: StackService
    compose: Optional[ComposeService]
    session: AsyncSession


async def get_stack_ctx(session: AsyncSession = Depends(get_db)) -> StackContext:
    all_settings = await settings_service.get_all(session)
    docker = Docker(get_client(all_settings["docker_host"]))
    cli = await get_cli_info(all_settings["docker_cli_path"])
    compose = None
    if cli:
        executor = stack_tasks.get_executor(all_settings["docker_host"])
        compose = ComposeService(cli, executor)
    return StackContext(
        stack=StackService(docker, settings.dockore_stacks_dir),
        compose=compose,
        session=session,
    )
