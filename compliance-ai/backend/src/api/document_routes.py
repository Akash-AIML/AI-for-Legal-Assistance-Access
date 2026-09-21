"""Document management routes (admin: upload, inspect, re-index, delete)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from auth import get_current_user, get_optional_user
from ingestion import store
from ingestion.ingestor import ingest_file
from models import DocMetadata, DocStatus

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"


class StatusUpdate(BaseModel):
    document_id: str
    status: DocStatus


def _admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("Admin", "Compliance", "HR"):
        from fastapi import HTTPException

        raise HTTPException(403, "Insufficient permissions")
    return user


@router.get("")
def list_documents(user: dict = Depends(get_optional_user)):
    username = user.get("username") if user else None
    return {"documents": store.list_documents(owner=username), "chunk_count": store.count_chunks()}


import time

@router.post("/upload")
async def upload(file: UploadFile = File(...), user: dict = Depends(get_optional_user)):
    t0 = time.time()
    print(f"\n\033[94m📁 [API-PERF] Document upload starting: {file.filename}\033[0m", flush=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / file.filename
    content = await file.read()
    target.write_bytes(content)
    t_ingest = time.time()
    username = user.get("username") if user else None
    count = ingest_file(target, owner=username)
    dt_total = (time.time() - t0) * 1000.0
    dt_ingest = (time.time() - t_ingest) * 1000.0
    print(f"\033[92m📁 [API-PERF] Upload complete: {file.filename} | Size: {len(content)} bytes | Ingestion: {dt_ingest:.1f}ms | Total: {dt_total:.1f}ms | Chunks: {count}\033[0m\n", flush=True)
    return {"filename": file.filename, "chunks_indexed": count}


@router.post("/status")
def update_status(body: StatusUpdate, user: dict = Depends(_admin)):
    # Rebuild metadata for every chunk of this document.
    ids = [
        cid
        for cid, m in store._meta_index.items()
        if m.get("document_id") == body.document_id
    ]
    if not ids:
        return {"error": "document not found"}
    col = store.get_collection()
    metas = col.get(ids=ids, include=["metadatas"])["metadatas"]
    for flat in metas:
        flat["status"] = body.status.value
    col.update(ids=ids, metadatas=metas)
    store.rebuild_index()
    return {"updated": len(ids), "status": body.status.value}


@router.delete("/{document_id}")
def delete_document(document_id: str, user: dict = Depends(_admin)):
    removed = store.delete_document(document_id)
    return {"removed": removed}


@router.post("/reindex")
def reindex(user: dict = Depends(_admin)):
    from ingestion.parser import SUPPORTED_EXT

    total = 0
    for d in (UPLOAD_DIR,):
        for p in sorted(d.glob("*")):
            if p.suffix.lower() in SUPPORTED_EXT:
                total += ingest_file(p)
    return {"reindexed_chunks": total}