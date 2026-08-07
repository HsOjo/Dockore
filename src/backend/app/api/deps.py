from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings_service
from app.core.database import get_db
from app.services.docker.client import Docker, get_client


async def resolve_docker(session: AsyncSession) -> Docker:
    """Build the Docker facade from the effective docker_host setting."""
    all_settings = await settings_service.get_all(session)
    return Docker(get_client(all_settings["docker_host"]))


async def get_docker(session: AsyncSession = Depends(get_db)) -> Docker:
    return await resolve_docker(session)
