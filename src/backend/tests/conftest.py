import asyncio
import hashlib
import os
import tempfile

os.environ["DOCKORE_TOKEN"] = "test-token"
os.environ["DOCKORE_DATA_DIR"] = tempfile.mkdtemp(prefix="dockore-test-")

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_docker
from app.core.database import engine
from app.main import app
from app.models import Base
from tests.fakes import FakeDocker

TOKEN = "test-token"
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()
AUTH = {"Authorization": f"Bearer {TOKEN_HASH}"}


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    # httpx ASGITransport does not run the lifespan, so create tables explicitly.
    async def run():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(run())


@pytest.fixture
async def client():
    fake = FakeDocker()
    app.dependency_overrides[get_docker] = lambda: fake
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
