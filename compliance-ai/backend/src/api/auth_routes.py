"""Auth and user routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import USERS, _hash, _verify, create_token, get_current_user, get_user_data
from memory import store as memory_store

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    role: str = "Citizen"
    department: str = "General"
    jurisdiction: str = "IN"


class LoginResponse(BaseModel):
    access_token: str
    user: dict


@router.post("/register", operation_id="register_user", response_model=LoginResponse, description="Register a new citizen user.")
def register(body: RegisterRequest) -> LoginResponse:
    username = body.username.strip().lower()
    if not username or not body.password:
        raise HTTPException(400, "Username and password are required")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    existing = get_user_data(username)
    if existing:
        raise HTTPException(400, "Username already registered")
    salt = uuid.uuid4().hex[:16]
    hashed_password = _hash(body.password, salt)
    memory_store.upsert_user(
        user_id=username,
        name=body.name,
        role=body.role,
        department=body.department,
        jurisdiction=body.jurisdiction,
        password_hash=hashed_password,
        salt=salt,
    )
    token = create_token(username)
    return LoginResponse(
        access_token=token,
        user={
            "username": username,
            "name": body.name,
            "role": body.role,
            "department": body.department,
            "jurisdiction": body.jurisdiction,
        },
    )


@router.post("/login", operation_id="login_user", response_model=LoginResponse, description="Authenticate with username and password to receive a JWT bearer token.")
def login(body: LoginRequest) -> LoginResponse:
    user = get_user_data(body.username)
    # Constant-time comparison using PBKDF2-HMAC-SHA256 with per-user salt
    if not user or not _verify(body.password, user["password"], user.get("salt", "")):
        raise HTTPException(401, "Invalid credentials")
    token = create_token(body.username)
    return LoginResponse(
        access_token=token,
        user={"username": body.username, **{k: v for k, v in user.items() if k not in ("password", "salt")}},
    )


@router.get("/me", operation_id="get_current_user_profile", description="Get the currently authenticated user's profile and role.")
def me(user: dict = Depends(get_current_user)) -> dict:
    return {"username": user["username"], "name": user["name"], "role": user["role"], "department": user["department"], "jurisdiction": user["jurisdiction"]}


@router.get("/users", operation_id="list_users", description="List all users. Requires Admin, Legal Aid Advisor, or Compliance role.")
def users(user: dict = Depends(get_current_user)) -> list:
    if user["role"] not in ("Admin", "Legal Aid Advisor", "Compliance", "HR"):
        raise HTTPException(403, "Insufficient permissions")
    db_users = memory_store.get_all_users()
    if db_users:
        return [
            {"username": u["id"], "name": u["name"], "role": u["role"], "department": u["department"], "jurisdiction": u["jurisdiction"]}
            for u in db_users
        ]
    return [
        {"username": u, "name": v["name"], "role": v["role"], "department": v["department"], "jurisdiction": v["jurisdiction"]}
        for u, v in USERS.items()
    ]