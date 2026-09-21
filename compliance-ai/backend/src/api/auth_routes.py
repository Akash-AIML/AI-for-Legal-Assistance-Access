"""Auth and user routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from auth import USERS, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: dict):
    username = payload.get("username", "")
    password = payload.get("password", "")
    user = USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(401, "Invalid credentials")
    token = create_token(username)
    return {"access_token": token, "user": {"username": username, **{k: v for k, v in user.items() if k != "password"}}}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "name": user["name"], "role": user["role"], "department": user["department"], "jurisdiction": user["jurisdiction"]}


@router.get("/users")
def users(user: dict = Depends(get_current_user)):
    if user["role"] not in ("Admin", "Compliance", "HR"):
        raise HTTPException(403, "Insufficient permissions")
    return [
        {"username": u, "name": v["name"], "role": v["role"], "department": v["department"], "jurisdiction": v["jurisdiction"]}
        for u, v in USERS.items()
    ]