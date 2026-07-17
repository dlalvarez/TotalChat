from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.config import get_settings

ACCESS_TOKEN_EXPIRES_SECONDS = 1800


class AuthTokenError(Exception):
    pass


def _secret() -> str:
    secret = get_settings().jwt_secret
    if not secret:
        raise AuthTokenError("TOTALCHAT_JWT_SECRET is required for admin authentication tokens.")
    return secret


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_access_token(*, user_id: UUID, email: str, now: datetime | None = None) -> tuple[str, int]:
    now = now or datetime.now(timezone.utc)
    exp = int((now + timedelta(seconds=ACCESS_TOKEN_EXPIRES_SECONDS)).timestamp())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(user_id), "email": email, "type": "access", "exp": exp}
    signing_input = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(_secret().encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(signature)}", ACCESS_TOKEN_EXPIRES_SECONDS


def decode_access_token(token: str, *, now: datetime | None = None) -> dict[str, object]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = _b64(hmac.new(_secret().encode(), signing_input.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, signature_b64):
            raise AuthTokenError("Invalid token signature.")
        header = json.loads(_unb64(header_b64))
        payload = json.loads(_unb64(payload_b64))
    except AuthTokenError:
        raise
    except Exception as exc:
        raise AuthTokenError("Invalid token.") from exc
    if header.get("alg") != "HS256" or payload.get("type") != "access":
        raise AuthTokenError("Invalid token.")
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise AuthTokenError("Invalid token.")
    if exp <= int((now or datetime.now(timezone.utc)).timestamp()):
        raise AuthTokenError("Token has expired.")
    if not payload.get("sub") or not payload.get("email"):
        raise AuthTokenError("Invalid token.")
    return payload
