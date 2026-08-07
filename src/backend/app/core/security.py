import hashlib
import hmac
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core import config

security = HTTPBearer(auto_error=False)

TERMINAL_TICKET_SALT = "dockore-terminal"


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of the provided token."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token_hash: str, expected_token: str) -> bool:
    """Compare an incoming token hash with the expected token hash in constant time."""
    return hmac.compare_digest(token_hash, hash_token(expected_token))


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(config.settings.dockore_token, salt=TERMINAL_TICKET_SALT)


def create_terminal_ticket(container_id: str, command: Optional[str]) -> str:
    """Sign a terminal session ticket for the given container."""
    return _serializer().dumps({"container_id": container_id, "command": command})


def verify_terminal_ticket(ticket: str, max_age: int) -> Optional[dict]:
    """Verify a terminal ticket, returning its payload or None if invalid/expired."""
    try:
        payload = _serializer().loads(ticket, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(payload, dict) or not payload.get("container_id"):
        return None
    return payload


async def get_current_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    # The client is expected to send the SHA-256 hash of the token in the
    # Authorization header (or query param for WebSocket) so the raw token is
    # never transmitted over the wire.
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization",
        )

    if not verify_token(token, config.settings.dockore_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return token
