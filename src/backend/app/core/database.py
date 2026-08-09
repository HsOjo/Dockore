from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import settings


def _enable_foreign_keys(dbapi_conn, connection_record):
    """Enable SQLite foreign key enforcement on every new connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine(url: str, **kwargs) -> AsyncEngine:
    """Create an async engine with SQLite foreign keys enabled."""
    eng = create_async_engine(url, **kwargs)
    event.listen(eng.sync_engine, "connect", _enable_foreign_keys)
    return eng


engine = create_engine(settings.db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
