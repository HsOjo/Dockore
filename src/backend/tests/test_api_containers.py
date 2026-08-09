from app.core.security import verify_terminal_ticket
from tests.conftest import AUTH
from tests.fakes import CONTAINER

CID = CONTAINER["id"]


async def test_list_containers(client):
    resp = await client.get("/api/containers", headers=AUTH)
    assert resp.status_code == 200
    items = resp.json()
    assert items[0]["id"] == CID
    assert items[0]["image"]["id"]


async def test_get_container(client):
    resp = await client.get(f"/api/containers/{CID}", headers=AUTH)
    assert resp.status_code == 200
    item = resp.json()
    assert item["network"]["ports"][0]["listen_port"] == 8080


async def test_get_container_not_found(client):
    resp = await client.get("/api/containers/missing", headers=AUTH)
    assert resp.status_code == 404


async def test_create_container(client):
    body = {
        "image": "nginx:latest",
        "command": "nginx",
        "name": "web2",
        "tty": True,
        "ports": [
            {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080}
        ],
        "volumes": [{"path": "data", "bind": "/data", "mode": "rw"}],
    }
    resp = await client.post("/api/containers", headers=AUTH, json=body)
    assert resp.status_code == 200
    assert resp.json()["id"] == CID


async def test_create_and_run_container(client):
    body = {"image": "nginx:latest", "command": "nginx"}
    resp = await client.post("/api/containers?run=true", headers=AUTH, json=body)
    assert resp.status_code == 200


async def test_delete_containers_collects_failures(client):
    resp = await client.request(
        "DELETE", "/api/containers", headers=AUTH, json={"ids": [CID, "bad"]}
    )
    assert resp.status_code == 200
    failed = resp.json()["failed"]
    assert "bad" in failed
    assert CID not in failed


async def test_container_operations(client):
    for op in ("start", "stop", "restart"):
        resp = await client.post(f"/api/containers/{CID}/{op}", headers=AUTH)
        assert resp.status_code == 200, op
    resp = await client.post(
        f"/api/containers/{CID}/stop?timeout=5", headers=AUTH
    )
    assert resp.status_code == 200
    resp = await client.post(
        f"/api/containers/{CID}/rename", headers=AUTH, json={"name": "web3"}
    )
    assert resp.status_code == 200


async def test_container_logs(client):
    resp = await client.get(f"/api/containers/{CID}/logs", headers=AUTH)
    assert resp.status_code == 200
    assert resp.text == "log line\n"


async def test_container_diff(client):
    resp = await client.get(f"/api/containers/{CID}/diff", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == {
        "add": ["/new"],
        "change": ["/etc"],
        "delete": [],
        "other": [],
    }


async def test_container_commit(client):
    resp = await client.post(
        f"/api/containers/{CID}/commit",
        headers=AUTH,
        json={"name": "web-image", "tag": "v1"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"]


async def test_container_exec(client):
    resp = await client.post(
        f"/api/containers/{CID}/exec", headers=AUTH, json={"command": "ls"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"exit_code": 0, "output": "ok\n"}


async def test_container_terminal_ticket(client):
    resp = await client.post(
        f"/api/containers/{CID}/terminal",
        headers=AUTH,
        json={"command": "/bin/bash"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["expires"] == 3600
    payload = verify_terminal_ticket(data["ticket"], max_age=3600)
    assert payload == {"container_id": CID, "command": "/bin/bash"}


async def test_container_terminal_ticket_not_found(client):
    resp = await client.post(
        "/api/containers/missing/terminal", headers=AUTH, json={}
    )
    assert resp.status_code == 404
