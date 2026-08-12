from types import SimpleNamespace

from tests.conftest import AUTH
from tests.fakes import IMAGE

IID = IMAGE["id"]


async def test_list_images(client):
    resp = await client.get("/api/images", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == IID


async def test_get_image(client):
    resp = await client.get(f"/api/images/{IID}", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["architecture"] == "amd64"


async def test_get_image_not_found(client):
    resp = await client.get("/api/images/missing", headers=AUTH)
    assert resp.status_code == 404


async def test_delete_images(client):
    resp = await client.request(
        "DELETE",
        "/api/images",
        headers=AUTH,
        json={"ids": [IID, "bad"], "tag_only": True},
    )
    assert resp.status_code == 200
    failed = resp.json()["failed"]
    assert "bad" in failed
    assert IID not in failed


async def test_pull_image(client, monkeypatch):
    started = []

    class _PullTasks:
        async def start(self, docker_host, name, tag):
            started.append((docker_host, name, tag))
            return SimpleNamespace(id="pull-1")

    monkeypatch.setattr("app.api.image.pull_tasks", _PullTasks())
    resp = await client.post(
        "/api/images/pull", headers=AUTH, json={"name": "nginx", "tag": "latest"}
    )
    assert resp.status_code == 200
    assert resp.json()["pull_id"] == "pull-1"
    assert started == [("", "nginx", "latest")]


async def test_pull_image_conflict_when_busy(client, monkeypatch):
    class _BusyPullTasks:
        async def start(self, docker_host, name, tag):
            return None

    monkeypatch.setattr("app.api.image.pull_tasks", _BusyPullTasks())
    resp = await client.post(
        "/api/images/pull", headers=AUTH, json={"name": "nginx", "tag": "latest"}
    )
    assert resp.status_code == 409


async def test_tag_image(client):
    resp = await client.post(
        f"/api/images/{IID}/tag",
        headers=AUTH,
        json={"name": "my-nginx", "tag": "v1"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"success": True}


async def test_image_history(client):
    resp = await client.get(f"/api/images/{IID}/history", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["created_by"]


async def test_image_search(client):
    resp = await client.get("/api/images/search/nginx", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "nginx"
