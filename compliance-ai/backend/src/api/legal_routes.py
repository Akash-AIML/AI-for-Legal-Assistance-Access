"""Legal analysis API routes: X-Ray, Compare, Lawyer Brief, Obligations."""
from __future__ import annotations

from datetime import date
from typing import Any

import anyio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user, get_optional_user
from ingestion import store
from legal_engine import analyze_document, compare_documents, generate_lawyer_brief
from memory import store as memory_store
from models import AuthorityType, DocMetadata, DocStatus, RetrievedEvidence

router = APIRouter(prefix="/api/legal", tags=["Legal Document Analysis"])


class AnalyzeRequest(BaseModel):
    document_id: str
    language: str = "en"


class CompareRequest(BaseModel):
    document_a: str
    document_b: str


class BriefRequest(BaseModel):
    document_id: str
    language: str = "en"


class ObligationsRequest(BaseModel):
    document_id: str


# In-memory object cache for raw result models
_xray_obj_cache: dict[str, Any] = {}


def _chunks_for_doc(document_id: str, user: dict | None = None) -> list[RetrievedEvidence]:
    """Retrieve all chunks belonging to a document with multi-tenant ownership check."""
    raw_chunks = store.get_chunks_for_doc(document_id)
    chunks = []
    doc_owner = None
    for cid, meta, text in raw_chunks:
        if doc_owner is None:
            doc_owner = meta.get("owner")
        chunks.append(
            RetrievedEvidence(
                chunk_id=cid,
                doc_id=document_id,
                section=meta.get("section", "Body"),
                text=text,
                metadata=store.flat_to_doc_metadata(meta),
                fusion_score=0.0,
            )
        )

    # Multi-tenant document privacy: verify that the requesting user owns the document or has elevated role
    if chunks and doc_owner and doc_owner not in ("global", "demo", "public_user", None):
        if not user or not user.get("username"):
            raise HTTPException(403, "Access denied: Authentication required to access private document.")
        current_username = user.get("username")
        is_elevated = user.get("role") in ("Admin", "Legal Aid Advisor")
        if not is_elevated and current_username != doc_owner:
            raise HTTPException(403, "Access denied: You do not have permission to access this document.")

    # Sort by section index for coherent analysis
    chunks.sort(key=lambda e: e.section)
    return chunks


@router.post("/analyze", operation_id="analyze_document_xray", description="Run Document X-Ray analysis on an indexed document.")
@router.post("/xray", operation_id="xray_document_alias", description="Alias for Document X-Ray analysis.")
async def analyze(body: AnalyzeRequest, user: dict = Depends(get_optional_user)) -> dict:
    """Run Document X-Ray analysis on an indexed document."""
    document_id = body.document_id.strip()
    if not document_id:
        raise HTTPException(400, "document_id is required")

    chunks = _chunks_for_doc(document_id, user=user)
    if not chunks:
        raise HTTPException(404, f"Document {document_id} not found in index")

    # Return cached X-Ray result from persistent SQLite store if available (checked only after permission validation)
    cached_xray = memory_store.get_xray_cache(document_id, language=body.language)
    if cached_xray:
        return cached_xray

    title = chunks[0].metadata.title if chunks else document_id
    result = await anyio.to_thread.run_sync(analyze_document, document_id, title, chunks, body.language)

    resp_data = {
        "document_id": result.document_id,
        "title": result.title,
        "overall_risk": result.overall_risk.value,
        "summary": result.summary,
        "findings": [
            {
                "clause_type": f.clause_type.value,
                "severity": f.severity.value,
                "section": f.section,
                "title": f.title,
                "explanation": f.explanation,
                "source_text": f.source_text,
                "why_it_matters": f.why_it_matters,
                "lawyer_question": f.lawyer_question,
            }
            for f in result.findings
        ],
        "obligations": [
            {
                "subject": o.subject,
                "action": o.action,
                "deadline": o.deadline,
                "condition": o.condition,
                "source_section": o.source_section,
                "consequence": o.consequence,
            }
            for o in result.obligations
        ],
        "lawyer_questions": result.lawyer_questions,
    }

    # Persist in SQLite cache and in-memory object cache
    memory_store.set_xray_cache(document_id, resp_data, language=body.language)
    _xray_obj_cache[document_id] = result
    return resp_data


@router.post("/compare", operation_id="compare_legal_documents", description="Compare two indexed documents clause by clause.")
async def compare(body: CompareRequest, user: dict = Depends(get_optional_user)) -> dict:
    """Compare two indexed documents clause by clause."""
    doc_a_id = body.document_a.strip()
    doc_b_id = body.document_b.strip()

    if not doc_a_id or not doc_b_id:
        raise HTTPException(400, "Both document_a and document_b are required")
    if doc_a_id == doc_b_id:
        raise HTTPException(400, "Cannot compare a document with itself")

    # Fast persistent SQLite cache lookup (sub-5ms response time)
    cached_compare = memory_store.get_compare_cache(doc_a_id, doc_b_id)
    if cached_compare:
        return cached_compare

    chunks_a = _chunks_for_doc(doc_a_id, user=user)
    chunks_b = _chunks_for_doc(doc_b_id, user=user)

    if not chunks_a:
        raise HTTPException(404, f"Document {doc_a_id} not found in index")
    if not chunks_b:
        raise HTTPException(404, f"Document {doc_b_id} not found in index")

    title_a = chunks_a[0].metadata.title if chunks_a else doc_a_id
    title_b = chunks_b[0].metadata.title if chunks_b else doc_b_id

    result = await anyio.to_thread.run_sync(compare_documents, doc_a_id, title_a, chunks_a, doc_b_id, title_b, chunks_b)

    resp_data = {
        "document_a_id": result.document_a_id,
        "document_b_id": result.document_b_id,
        "document_a_title": result.document_a_title,
        "document_b_title": result.document_b_title,
        "comparisons": [
            {
                "clause_type": c.clause_type.value,
                "document_a_text": c.document_a_text,
                "document_b_text": c.document_b_text,
                "status": c.status,
                "impact": c.impact,
            }
            for c in result.comparisons
        ],
        "summary": result.summary,
    }

    # Persist in SQLite compare cache
    memory_store.set_compare_cache(doc_a_id, doc_b_id, resp_data)
    return resp_data


@router.post("/lawyer-brief", operation_id="generate_lawyer_brief", description="Generate a pre-consultation lawyer brief for a document.")
async def lawyer_brief(body: BriefRequest, user: dict = Depends(get_optional_user)) -> dict:
    """Generate a pre-consultation lawyer brief for a document."""
    document_id = body.document_id.strip()
    if not document_id:
        raise HTTPException(400, "document_id is required")

    # Fast persistent SQLite cache lookup (sub-5ms response time)
    cached_brief = memory_store.get_brief_cache(document_id, language=body.language)
    if cached_brief:
        return cached_brief

    chunks = _chunks_for_doc(document_id, user=user)
    if not chunks:
        raise HTTPException(404, f"Document {document_id} not found in index")

    title = chunks[0].metadata.title if chunks else document_id

    # Reuse cached X-Ray if available to save redundant LLM call
    if document_id in _xray_obj_cache:
        xray = _xray_obj_cache[document_id]
    else:
        xray = await anyio.to_thread.run_sync(analyze_document, document_id, title, chunks, body.language)
        _xray_obj_cache[document_id] = xray

    # Generate the lawyer brief with requested language (e.g. English or Hindi)
    brief = await anyio.to_thread.run_sync(generate_lawyer_brief, document_id, title, xray, body.language)

    resp_data = {
        "document_id": brief.document_id,
        "situation": brief.situation,
        "key_clauses": brief.key_clauses,
        "risk_areas": brief.risk_areas,
        "recommended_questions": brief.recommended_questions,
        "information_to_gather": brief.information_to_gather,
    }

    # Persist in SQLite brief cache
    memory_store.set_brief_cache(document_id, resp_data, language=body.language)
    return resp_data


@router.post("/obligations", operation_id="extract_document_obligations", description="Extract obligations and deadlines from a document.")
async def obligations(body: ObligationsRequest, user: dict = Depends(get_optional_user)) -> dict:
    """Extract obligations and deadlines from a document."""
    document_id = body.document_id.strip()
    if not document_id:
        raise HTTPException(400, "document_id is required")

    # Reuse cached X-Ray obligations if available from SQLite
    cached = memory_store.get_xray_cache(document_id)
    if cached:
        return {
            "document_id": document_id,
            "title": cached.get("title", document_id),
            "obligations": cached.get("obligations", []),
        }

    chunks = _chunks_for_doc(document_id, user=user)
    if not chunks:
        raise HTTPException(404, f"Document {document_id} not found in index")

    title = chunks[0].metadata.title if chunks else document_id
    xray = await anyio.to_thread.run_sync(analyze_document, document_id, title, chunks)
    _xray_obj_cache[document_id] = xray

    return {
        "document_id": document_id,
        "title": title,
        "obligations": [
            {
                "subject": o.subject,
                "action": o.action,
                "deadline": o.deadline,
                "condition": o.condition,
                "source_section": o.source_section,
                "consequence": o.consequence,
            }
            for o in xray.obligations
        ],
    }


@router.get("/documents", operation_id="list_analyzable_documents", description="List all documents available for analysis.")
def list_analyzable(user: dict = Depends(get_optional_user)) -> dict:
    """List all documents available for analysis."""
    username = user.get("username") if user else None
    docs = store.list_documents(owner=username)
    return {"documents": docs}


