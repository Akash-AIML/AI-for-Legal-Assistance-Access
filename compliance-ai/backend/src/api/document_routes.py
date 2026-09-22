"""Document management routes (admin: upload, inspect, re-index, delete)."""
from __future__ import annotations

import logging
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from auth import get_current_user, get_optional_user
from ingestion import store
from ingestion.ingestor import ingest_file
from models import DocMetadata, DocStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Policy Documents & Governance"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(tempfile.gettempdir()) / "legal_lens_uploads")))
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class StatusUpdate(BaseModel):
    document_id: str
    status: DocStatus


def _admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("Admin", "Legal Aid Advisor", "Compliance", "HR"):
        raise HTTPException(403, "Insufficient permissions")
    return user


@router.get("", operation_id="list_documents", description="List all indexed policy documents and total chunk count.")
def list_documents(user: dict = Depends(get_optional_user)) -> dict:
    username = user.get("username") if user else None
    return {"documents": store.list_documents(owner=username), "chunk_count": store.count_chunks()}


@router.post("/upload", operation_id="upload_document", description="Upload a PDF, DOCX, TXT, or Markdown document for vector indexing.")
async def upload(file: UploadFile = File(...), user: dict = Depends(get_optional_user)) -> dict:
    t0 = time.time()
    logger.info("Document upload starting: %s", file.filename)

    # Validate file extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Path traversal protection: strip directory components, sanitize filename, and verify path boundary
    raw_name = os.path.basename(file.filename or "upload")
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", raw_name).lstrip(".").replace("..", "_") or "upload"
    unique_prefix = uuid.uuid4().hex[:8]
    target = (UPLOAD_DIR / f"{unique_prefix}_{safe_name}").resolve()
    if not str(target).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(400, "Invalid file path: path traversal detected.")

    content = await file.read()

    # Enforce max upload size
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024*1024)} MB.")

    # Magic byte and content validation to prevent disguised malicious files
    if ext == ".pdf" and not content.startswith(b"%PDF"):
        raise HTTPException(400, "File content is not a valid PDF.")
    elif ext == ".docx" and not content.startswith(b"PK\x03\x04"):
        raise HTTPException(400, "File content is not a valid DOCX.")
    elif ext in (".txt", ".md"):
        if content.startswith(b"MZ") or content.startswith(b"\x7fELF") or b"\x00" in content[:1024]:
            raise HTTPException(400, f"File contents do not match expected format for '{ext}' (binary or executable content detected).")
        try:
            content[:4096].decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(400, f"File contents cannot be decoded as valid UTF-8 text for '{ext}'.")

    target.write_bytes(content)
    t_ingest = time.time()
    username = user.get("username") if user else None
    count = ingest_file(target, owner=username)
    dt_total = (time.time() - t0) * 1000.0
    dt_ingest = (time.time() - t_ingest) * 1000.0
    logger.info(
        "Upload complete: %s | size=%d bytes | ingestion=%.1fms | total=%.1fms | chunks=%d",
        file.filename, len(content), dt_ingest, dt_total, count,
    )
    return {"filename": file.filename, "chunks_indexed": count}



@router.post("/status", operation_id="update_document_status", description="Update the governance status (ACTIVE, SUPERSEDED, etc.) of a policy document.")
def update_status(body: StatusUpdate, user: dict = Depends(_admin)) -> dict:
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


@router.delete("/{document_id}", operation_id="delete_document", description="Permanently delete a document and all its indexed chunks.")
def delete_document(document_id: str, user: dict = Depends(_admin)) -> dict:
    removed = store.delete_document(document_id)
    return {"removed": removed}


@router.post("/reindex", operation_id="reindex_documents", description="Re-index all documents in the upload directory.")
def reindex(user: dict = Depends(_admin)) -> dict:
    from ingestion.parser import SUPPORTED_EXT

    total = 0
    for d in (UPLOAD_DIR,):
        for p in sorted(d.glob("*")):
            if p.suffix.lower() in SUPPORTED_EXT:
                total += ingest_file(p)
    return {"reindexed_chunks": total}