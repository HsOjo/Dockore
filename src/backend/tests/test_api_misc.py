from httpx import ASGITransport, AsyncClient

from app.api.deps import get_docker
from app.main import app
from app.services.cli import DockerApiError, DockerError, DockerNotFound
from tests.conftest import AUTH


class _Boom:
    def __init__(self, exc):
        self._exc = exc

    async def list(self, **kwargs):
        raise self._exc


class _Docker:
    def __init__(self, exc):
        self.container = _Boom(exc)


async def _request_with(exc):
    app.dependency_overrides[get_docker] = lambda: _Docker(exc)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            return await c.get("/api/containers", headers=AUTH)
    finally:
        app.dependency_overrides.clear()


async def test_docker_error_maps_to_502():
    resp = await _request_with(DockerError("cannot connect"))
    assert resp.status_code == 502
    assert "cannot connect" in resp.json()["detail"]


async def test_docker_api_error_maps_to_400():
    resp = await _request_with(DockerApiError("bad request"))
    assert resp.status_code == 400


async def test_docker_not_found_maps_to_404():
    resp = await _request_with(DockerNotFound("gone"))
    assert resp.status_code == 404


async def test_health_no_auth(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_auth_validate(client):
    resp = await client.get("/api/auth/validate", headers=AUTH)
    assert resp.status_code == 200

    resp = await client.get("/api/auth/validate")
    assert resp.status_code == 401

    resp = await client.get(
        "/api/auth/validate", headers={"Authorization": "Bearer wrong"}
    )
    assert resp.status_code == 401


async def test_protected_endpoint_requires_auth(client):
    resp = await client.get("/api/containers")
    assert resp.status_code == 401


async def test_system_version(client):
    resp = await client.get("/api/system/version", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "project" in data
    assert "docker" in data


async def test_query_token_auth(client):
    from tests.conftest import TOKEN_HASH

    resp = await client.get(f"/api/auth/validate?token={TOKEN_HASH}")
    assert resp.status_code == 200
