from tests.conftest import AUTH
from tests.fakes import CONTAINER, NETWORK, VOLUME

NID = NETWORK["id"]
VID = VOLUME["id"]


async def test_list_networks(client):
    resp = await client.get("/api/networks", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == NID


async def test_get_network(client):
    resp = await client.get(f"/api/networks/{NID}", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["subnet"] == "172.17.0.0/16"


async def test_get_network_not_found(client):
    resp = await client.get("/api/networks/missing", headers=AUTH)
    assert resp.status_code == 404


async def test_create_network(client):
    body = {
        "name": "mynet",
        "driver": "bridge",
        "attachable": True,
        "options": [{"key": "mtu", "value": "1500"}],
        "subnet": "10.0.0.0/24",
        "gateway": "10.0.0.1",
    }
    resp = await client.post("/api/networks", headers=AUTH, json=body)
    assert resp.status_code == 200
    assert resp.json()["id"] == NID


async def test_delete_networks(client):
    resp = await client.request(
        "DELETE", "/api/networks", headers=AUTH, json={"ids": [NID, "bad"]}
    )
    assert resp.status_code == 200
    failed = resp.json()["failed"]
    assert "bad" in failed
    assert NID not in failed


async def test_connect_disconnect_network(client):
    resp = await client.post(
        f"/api/networks/{NID}/connect",
        headers=AUTH,
        json={"container_id": CONTAINER["id"]},
    )
    assert resp.status_code == 200
    resp = await client.post(
        f"/api/networks/{NID}/disconnect?force=true",
        headers=AUTH,
        json={"container_id": CONTAINER["id"]},
    )
    assert resp.status_code == 200


async def test_list_volumes(client):
    resp = await client.get("/api/volumes", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == VID


async def test_get_volume(client):
    resp = await client.get(f"/api/volumes/{VID}", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["name"] == "data"


async def test_get_volume_not_found(client):
    resp = await client.get("/api/volumes/missing", headers=AUTH)
    assert resp.status_code == 404


async def test_create_volume(client):
    body = {
        "name": "data2",
        "driver": "local",
        "driver_opts": [{"key": "type", "value": "none"}],
    }
    resp = await client.post("/api/volumes", headers=AUTH, json=body)
    assert resp.status_code == 200
    assert resp.json()["id"] == VID


async def test_delete_volumes(client):
    resp = await client.request(
        "DELETE", "/api/volumes", headers=AUTH, json={"ids": [VID, "bad"]}
    )
    assert resp.status_code == 200
    failed = resp.json()["failed"]
    assert "bad" in failed
    assert VID not in failed


async def test_system_version(client):
    resp = await client.get("/api/system/version", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"]["version"]
    assert data["project"]["python"]
    assert data["docker"]["engine"]["version"] == "24.0.0"
