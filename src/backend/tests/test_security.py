from app.core.security import (
    create_terminal_ticket,
    hash_token,
    verify_terminal_ticket,
    verify_token,
)
from tests.conftest import AUTH, TOKEN, TOKEN_HASH


def test_hash_and_verify_token():
    assert hash_token(TOKEN) == TOKEN_HASH
    assert verify_token(TOKEN_HASH, TOKEN)
    assert not verify_token(hash_token("wrong"), TOKEN)


def test_terminal_ticket_roundtrip():
    ticket = create_terminal_ticket("abc123", "/bin/bash")
    payload = verify_terminal_ticket(ticket, max_age=3600)
    assert payload == {"container_id": "abc123", "command": "/bin/bash"}


def test_terminal_ticket_expired():
    ticket = create_terminal_ticket("abc123", None)
    assert verify_terminal_ticket(ticket, max_age=-1) is None


def test_terminal_ticket_invalid():
    assert verify_terminal_ticket("not-a-ticket", max_age=3600) is None


async def test_health_no_auth(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_validate_requires_auth(client):
    resp = await client.get("/api/auth/validate")
    assert resp.status_code == 401


async def test_validate_with_token(client):
    resp = await client.get("/api/auth/validate", headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == {"valid": True}


async def test_validate_with_wrong_token(client):
    resp = await client.get(
        "/api/auth/validate", headers={"Authorization": f"Bearer {hash_token('x')}"}
    )
    assert resp.status_code == 401


async def test_protected_endpoint_requires_auth(client):
    resp = await client.get("/api/containers")
    assert resp.status_code == 401
