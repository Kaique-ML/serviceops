import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from serviceops.domain.models import Membership, Role, User
from serviceops.settings import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    # 16 MiB is compatible with constrained containers while remaining deliberately expensive.
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    salt_text = base64.urlsafe_b64encode(salt).decode()
    digest_text = base64.urlsafe_b64encode(digest).decode()
    return f"scrypt$16384$8$1${salt_text}${digest_text}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, n, r, p, salt, expected = encoded.split("$")
        actual = hashlib.scrypt(
            password.encode(), salt=base64.urlsafe_b64decode(salt), n=int(n), r=int(r), p=int(p)
        )
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False


def _sign(data: bytes) -> str:
    return hmac.new(get_settings().session_secret.encode(), data, hashlib.sha256).hexdigest()


def make_session(user_id: str, workspace_id: str) -> str:
    raw = json.dumps({"u": user_id, "w": workspace_id}, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(raw).decode()
    return f"{encoded}.{_sign(encoded.encode())}"


def parse_session(value: str | None) -> dict[str, str] | None:
    if not value or "." not in value:
        return None
    encoded, signature = value.rsplit(".", 1)
    if not hmac.compare_digest(signature, _sign(encoded.encode())):
        return None
    try:
        value = json.loads(base64.urlsafe_b64decode(encoded))
        return value if set(value) == {"u", "w"} else None
    except (ValueError, json.JSONDecodeError):
        return None


@dataclass(frozen=True)
class Principal:
    user_id: str
    workspace_id: str
    role: Role
    customer_id: str | None


def principal_from(request: Request, db: Session) -> Principal:
    data = parse_session(request.cookies.get("serviceops_session"))
    if not data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication_required")
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == data["u"],
            Membership.workspace_id == data["w"],
            Membership.active.is_(True),
        )
    )
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "membership_inactive")
    return Principal(
        membership.user_id, membership.workspace_id, membership.role, membership.customer_id
    )


def require_csrf(request: Request) -> None:
    cookie = request.cookies.get("serviceops_csrf")
    header = request.headers.get("x-csrf-token")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "csrf_failed")


def public_user(user: User, membership: Membership) -> dict[str, Any]:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "workspace_id": membership.workspace_id,
        "role": membership.role.value,
        "customer_id": membership.customer_id,
    }
