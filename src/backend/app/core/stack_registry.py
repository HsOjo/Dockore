from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StackRegistration


async def list_all(session: AsyncSession) -> list[StackRegistration]:
    rows = await session.execute(select(StackRegistration))
    return list(rows.scalars())


async def get(session: AsyncSession, name: str) -> Optional[StackRegistration]:
    rows = await session.execute(
        select(StackRegistration).where(StackRegistration.name == name)
    )
    return rows.scalars().first()


async def register(
    session: AsyncSession,
    name: str,
    path: str,
    config_files: str,
    source: str,
) -> StackRegistration:
    entry = StackRegistration(
        name=name, path=path, config_files=config_files, source=source,
    )
    session.add(entry)
    await session.commit()
    return entry


async def unregister(session: AsyncSession, name: str) -> bool:
    entry = await get(session, name)
    if not entry:
        return False
    await session.delete(entry)
    await session.commit()
    return True
