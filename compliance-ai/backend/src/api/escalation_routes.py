"""Escalation routes: employee view + admin resolution."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from memory import store as memory

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


class ResolveBody(BaseModel):
    escalation_id: str
    resolution: str


@router.get("")
def list_escalations(status: str | None = None, user: dict = Depends(get_current_user)):
    if user["role"] in ("Admin", "Compliance", "HR"):
        return {"escalations": memory.list_escalations(status)}
    # employees see only their own
    mine = [e for e in memory.list_escalations(status) if e["user_id"] == user["username"]]
    return {"escalations": mine}


@router.post("/resolve")
def resolve(body: ResolveBody, user: dict = Depends(get_current_user)):
    if user["role"] not in ("Admin", "Compliance", "HR"):
        from fastapi import HTTPException

        raise HTTPException(403, "Only HR/Compliance/Admin can resolve escalations")
    ok = memory.resolve_escalation(body.escalation_id, body.resolution)
    return {"resolved": ok}