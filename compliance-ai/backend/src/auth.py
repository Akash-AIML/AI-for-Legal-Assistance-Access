"""JWT authentication + simple RBAC with hardcoded demo users."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import get_settings
from models import ConversationFrame

_settings = get_settings()

# Demo users: {username: {password, name, role, department, jurisdiction}}
USERS = {
    "asha": {"password": "demo123", "name": "Asha Rao", "role": "Employee", "department": "Engineering", "jurisdiction": "IN"},
    "kenji": {"password": "demo123", "name": "Kenji Sato", "role": "Employee", "department": "Engineering", "jurisdiction": "DE"},
    "maria": {"password": "demo123", "name": "Maria Lopez", "role": "Manager", "department": "Engineering", "jurisdiction": "IN"},
    "priya": {"password": "demo123", "name": "Priya Menon", "role": "HR", "department": "People Ops", "jurisdiction": "IN"},
    "marcus": {"password": "demo123", "name": "Marcus Webb", "role": "Compliance", "department": "Compliance", "jurisdiction": "US"},
    "admin": {"password": "demo123", "name": "Admin User", "role": "Admin", "department": "IT", "jurisdiction": "Global"},
}

ROLE_HIERARCHY = ["Employee", "Manager", "HR", "Compliance", "Admin"]


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
    user = USERS.get(username or "")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return {"username": username, **user}


def get_optional_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        return {"username": "public_user", "name": "Public User", "role": "Employee", "department": "Public", "jurisdiction": "IN"}
    username = decode_token(creds.credentials)
    user = USERS.get(username or "")
    if not user:
        return {"username": "public_user", "name": "Public User", "role": "Employee", "department": "Public", "jurisdiction": "IN"}
    return {"username": username, **user}


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