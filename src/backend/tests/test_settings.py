from app.core.settings_service import ProxyConfig, proxy_from_settings
from app.services.cli.env import build_env
from tests.conftest import AUTH


async def test_get_default_settings(client):
    resp = await client.get("/api/settings", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert data["docker_host"] == "unix:///var/run/docker.sock"
    assert data["http_proxy"] == ""
    assert data["https_proxy"] == ""
    assert data["no_proxy"] == ""
    assert data["proxy_cli"] is True
    assert data["proxy_outbound"] is True


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


async def test_update_proxy_settings(client):
    resp = await client.put(
        "/api/settings",
        headers=AUTH,
        json={
            "http_proxy": "http://127.0.0.1:7890",
            "https_proxy": "http://127.0.0.1:7890",
            "no_proxy": "localhost,127.0.0.1",
            "proxy_cli": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["http_proxy"] == "http://127.0.0.1:7890"
    assert data["no_proxy"] == "localhost,127.0.0.1"
    assert data["proxy_cli"] is False
    assert data["proxy_outbound"] is True

    resp = await client.get("/api/settings", headers=AUTH)
    assert resp.json()["proxy_cli"] is False


def test_proxy_from_settings_scope_toggle():
    all_settings = {
        "http_proxy": "http://127.0.0.1:7890",
        "https_proxy": "",
        "no_proxy": "localhost",
        "proxy_cli": "false",
        "proxy_outbound": "true",
    }
    assert proxy_from_settings(all_settings, "cli") == ProxyConfig()
    outbound = proxy_from_settings(all_settings, "outbound")
    assert outbound.http_proxy == "http://127.0.0.1:7890"
    assert outbound.url == "http://127.0.0.1:7890"
    assert proxy_from_settings({}, "cli") == ProxyConfig()


def test_build_env_injects_proxy(monkeypatch):
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("http_proxy", raising=False)
    proxy = ProxyConfig(
        http_proxy="http://127.0.0.1:7890",
        https_proxy="http://127.0.0.1:7891",
        no_proxy="localhost",
    )
    env = build_env("tcp://127.0.0.1:2375", proxy)
    assert env["DOCKER_HOST"] == "tcp://127.0.0.1:2375"
    assert env["HTTP_PROXY"] == "http://127.0.0.1:7890"
    assert env["http_proxy"] == "http://127.0.0.1:7890"
    assert env["HTTPS_PROXY"] == "http://127.0.0.1:7891"
    assert env["NO_PROXY"] == "localhost"
    assert env["no_proxy"] == "localhost"

    env = build_env("")
    assert "DOCKER_HOST" not in env
    assert "HTTP_PROXY" not in env
