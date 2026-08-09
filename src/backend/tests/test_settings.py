from tests.conftest import AUTH


async def test_get_default_settings(client):
    resp = await client.get("/api/settings", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["docker_host"] == "unix:///var/run/docker.sock"


async def test_update_settings(client):
    resp = await client.put(
        "/api/settings", headers=AUTH, json={"docker_host": "tcp://127.0.0.1:2375"}
    )
    assert resp.status_code == 200
    assert resp.json()["docker_host"] == "tcp://127.0.0.1:2375"

    resp = await client.get("/api/settings", headers=AUTH)
    assert resp.json()["docker_host"] == "tcp://127.0.0.1:2375"


async def test_update_settings_empty_body_keeps_values(client):
    resp = await client.put("/api/settings", headers=AUTH, json={})
    assert resp.status_code == 200
    assert resp.json()["docker_host"] == "tcp://127.0.0.1:2375"


async def test_settings_require_auth(client):
    assert (await client.get("/api/settings")).status_code == 401
    assert (await client.put("/api/settings", json={})).status_code == 401
