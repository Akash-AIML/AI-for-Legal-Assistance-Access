"""JWT authentication + simple RBAC with hashed demo users."""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import get_settings
from models import ConversationFrame

_settings = get_settings()


def _hash(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256 with 100,000 iterations (OWASP/NIST compliant)."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def _verify(plain: str, hashed: str, salt: str = "") -> bool:
    """Constant-time comparison with PBKDF2."""
    if not salt:
        return False
    computed = _hash(plain, salt)
    return hmac.compare_digest(computed, hashed)


# Demo users — passwords hashed with per-user unique salts via PBKDF2 (100k iterations)
# All demo users use password: "demo123"
# Personas: Citizen Legal Aid & Assistance
_SALT_ASHA = "salt_asha_citizen_91a"
_SALT_KENJI = "salt_kenji_freelance_82b"
_SALT_MARIA = "salt_maria_business_73c"
_SALT_PRIYA = "salt_priya_advocate_64d"
_SALT_ADMIN = "salt_admin_legallens_55e"

USERS: dict[str, dict] = {
    "asha": {
        "password": _hash("demo123", _SALT_ASHA),
        "salt": _SALT_ASHA,
        "name": "Asha Rao",
        "role": "Citizen",
        "department": "Tenancy & Housing",
        "jurisdiction": "IN",
    },
    "kenji": {
        "password": _hash("demo123", _SALT_KENJI),
        "salt": _SALT_KENJI,
        "name": "Kenji Sato",
        "role": "Freelancer",
        "department": "Independent Work",
        "jurisdiction": "DE",
    },
    "maria": {
        "password": _hash("demo123", _SALT_MARIA),
        "salt": _SALT_MARIA,
        "name": "Maria Lopez",
        "role": "Small Business",
        "department": "Commercial Contracts",
        "jurisdiction": "US",
    },
    "priya": {
        "password": _hash("demo123", _SALT_PRIYA),
        "salt": _SALT_PRIYA,
        "name": "Priya Menon",
        "role": "Legal Aid Advisor",
        "department": "Community Legal Clinic",
        "jurisdiction": "IN",
    },
    "admin": {
        "password": _hash("demo123", _SALT_ADMIN),
        "salt": _SALT_ADMIN,
        "name": "Admin User",
        "role": "Admin",
        "department": "Legal Operations",
        "jurisdiction": "Global",
    },
}

ROLE_HIERARCHY = ["Guest", "Citizen", "Freelancer", "Small Business", "Legal Aid Advisor", "Admin"]


def _sync_sqlite_users() -> None:
    """Ensure demo users are seeded into persistent SQLite database."""
    try:
        from memory import store as memory_store
        for uid, udata in USERS.items():
            if not memory_store.get_user_by_id(uid):
                memory_store.upsert_user(
                    user_id=uid,
                    name=udata["name"],
                    role=udata["role"],
                    department=udata["department"],
                    jurisdiction=udata["jurisdiction"],
                    password_hash=udata["password"],
                    salt=udata["salt"],
                )
    except Exception:
        pass


_sync_sqlite_users()


def get_user_data(username: str) -> dict | None:
    """Lookup user from persistent SQLite store with fallback to USERS dict."""
    try:
        from memory import store as memory_store
        u = memory_store.get_user_by_id(username)
        if u:
            return {
                "password": u["password_hash"],
                "salt": u["salt"],
                "name": u["name"],
                "role": u["role"],
                "department": u["department"],
                "jurisdiction": u["jurisdiction"],
            }
    except Exception:
        pass
    return USERS.get(username)


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=_settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, _settings.jwt_secret, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


_bearer = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    username = decode_token(creds.credentials)
    user = get_user_data(username or "")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return {"username": username, **user}


def get_optional_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        return {"username": "guest", "name": "Guest Citizen", "role": "Guest", "department": "Public", "jurisdiction": "Global", "is_authenticated": False}
    username = decode_token(creds.credentials)
    user = USERS.get(username or "")
    if not user:
        return {"username": "guest", "name": "Guest Citizen", "role": "Guest", "department": "Public", "jurisdiction": "Global", "is_authenticated": False}
    return {"username": username, "is_authenticated": True, **user}



def require_roles(*roles: str):
    def dep(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return dep


def to_frame(user: dict, session_id: str = "") -> ConversationFrame:
    return ConversationFrame(
        user_id=user["username"],
        role=user["role"],
        department=user["department"],
        jurisdiction=user["jurisdiction"],
        session_id=session_id,
    )