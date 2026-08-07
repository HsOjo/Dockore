from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Setting

DEFAULT_SETTINGS = {
    "docker_host": "unix:///var/run/docker.sock",
}


async def get_all(session: AsyncSession) -> dict[str, str]:
    """Return all settings merged with defaults; env vars take priority over the DB."""
    result = dict(DEFAULT_SETTINGS)
    rows = await session.execute(select(Setting))
    for row in rows.scalars():
        result[row.key] = row.value
    if settings.dockore_docker_host:
        result["docker_host"] = settings.dockore_docker_host
    return result


async def set_many(session: AsyncSession, data: dict[str, str]) -> None:
    rows = await session.execute(select(Setting).where(Setting.key.in_(data.keys())))
    existed = {row.key: row for row in rows.scalars()}
    for key, value in data.items():
        if key in existed:
            existed[key].value = value
        else:
            session.add(Setting(key=key, value=value))
    await session.commit()
