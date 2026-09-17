"""Legal analysis API routes: X-Ray, Compare, Lawyer Brief, Obligations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user, get_optional_user
from ingestion import store
from legal_engine import analyze_document, compare_documents, generate_lawyer_brief
from models import RetrievedEvidence

router = APIRouter(prefix="/api/legal", tags=["Legal Document Analysis"])


def _chunks_for_doc(document_id: str) -> list[RetrievedEvidence]:
    """Retrieve all chunks belonging to a document."""
    chunks = []
    for cid, meta in store._meta_index.items():
        if meta.get("document_id") == document_id:
            text = store.get_chunk_text(cid) or ""
            chunks.append(
                RetrievedEvidence(
                    chunk_id=cid,
                    doc_id=document_id,
                    section=meta.get("section", "Body"),
                    text=text,
                    metadata=store._flat_to_meta_external(meta) if hasattr(store, '_flat_to_meta_external') else _flat_to_meta(meta),
                    fusion_score=0.0,
                )
            )
    # Sort by section index for coherent analysis
    chunks.sort(key=lambda e: e.section)
    return chunks


def _flat_to_meta(flat: dict):
    """Convert flat metadata dict to DocMetadata (local copy to avoid circular import issues)."""
    from models import DocMetadata, DocStatus
    from datetime import date

    m = DocMetadata(
        document_id=flat.get("document_id", ""),
        title=flat.get("title", ""),
        document_type=flat.get("document_type", "CONTRACT"),
        department=flat.get("department", "Legal"),
        jurisdiction=flat.get("jurisdiction", "Global"),
        version=flat.get("version", "1"),
        status=DocStatus(flat.get("status", "UNKNOWN")),
        authority=flat.get("authority", "official"),
        source_path=flat.get("source_path", ""),
        access_roles=[r for r in (flat.get("access_roles", "") or "").split(",") if r],
        tags=[t for t in (flat.get("tags", "") or "").split(",") if t],
    )
    try:
        if flat.get("effective_date"):
            m.effective_date = date.fromisoformat(flat["effective_date"])
        if flat.get("review_date"):
            m.review_date = date.fromisoformat(flat["review_date"])
        if flat.get("expiry_date"):
            m.expiry_date = date.fromisoformat(flat["expiry_date"])
    except (ValueError, TypeError):
        pass
    # Extended fields
    m.governing_law = flat.get("governing_law", "")
    m.country = flat.get("country", "")
    m.state = flat.get("state", "")
    m.citation = flat.get("citation", "")
    authority_type = flat.get("authority_type", "USER_DOCUMENT")
    try:
        from models import AuthorityType
        m.authority_type = AuthorityType(authority_type)
    except ValueError:
        pass
    return m


@router.post("/analyze")
@router.post("/xray")
def analyze(payload: dict, user: dict = Depends(get_optional_user)):
    """Run Document X-Ray analysis on an indexed document."""
    document_id = payload.get("document_id", "").strip()
    if not document_id:
        raise HTTPException(400, "document_id is required")

    chunks = _chunks_for_doc(document_id)
    if not chunks:
        raise HTTPException(404, f"Document {document_id} not found in index")

    title = chunks[0].metadata.title if chunks else document_id
    result = analyze_document(document_id, title, chunks)

    return {
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


@router.post("/compare")
def compare(payload: dict, user: dict = Depends(get_optional_user)):
    """Compare two indexed documents clause by clause."""
    doc_a_id = payload.get("document_a", "").strip()
    doc_b_id = payload.get("document_b", "").strip()

    if not doc_a_id or not doc_b_id:
        raise HTTPException(400, "Both document_a and document_b are required")
    if doc_a_id == doc_b_id:
        raise HTTPException(400, "Cannot compare a document with itself")

    chunks_a = _chunks_for_doc(doc_a_id)
    chunks_b = _chunks_for_doc(doc_b_id)

    if not chunks_a:
        raise HTTPException(404, f"Document {doc_a_id} not found in index")
    if not chunks_b:
        raise HTTPException(404, f"Document {doc_b_id} not found in index")

    title_a = chunks_a[0].metadata.title if chunks_a else doc_a_id
    title_b = chunks_b[0].metadata.title if chunks_b else doc_b_id

    result = compare_documents(doc_a_id, title_a, chunks_a, doc_b_id, title_b, chunks_b)

    return {
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


@router.post("/lawyer-brief")
def lawyer_brief(payload: dict, user: dict = Depends(get_optional_user)):
    """Generate a pre-consultation lawyer brief for a document."""
    document_id = payload.get("document_id", "").strip()
    if not document_id:
        raise HTTPException(400, "document_id is required")

    chunks = _chunks_for_doc(document_id)
    if not chunks:
        raise HTTPException(404, f"Document {document_id} not found in index")

    title = chunks[0].metadata.title if chunks else document_id

    # First run X-Ray analysis
    xray = analyze_document(document_id, title, chunks)

    # Then generate the lawyer brief from the X-Ray
    brief = generate_lawyer_brief(document_id, title, xray)

    return {
        "document_id": brief.document_id,
        "situation": brief.situation,
        "key_clauses": brief.key_clauses,
        "risk_areas": brief.risk_areas,
        "recommended_questions": brief.recommended_questions,
        "information_to_gather": brief.information_to_gather,
    }


@router.post("/obligations")
def obligations(payload: dict, user: dict = Depends(get_optional_user)):
    """Extract obligations and deadlines from a document."""
    document_id = payload.get("document_id", "").strip()
    if not document_id:
        raise HTTPException(400, "document_id is required")

    chunks = _chunks_for_doc(document_id)
    if not chunks:
        raise HTTPException(404, f"Document {document_id} not found in index")

    title = chunks[0].metadata.title if chunks else document_id
    xray = analyze_document(document_id, title, chunks)

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


@router.get("/documents")
def list_analyzable(user: dict = Depends(get_optional_user)):
    """List all documents available for analysis."""
    docs = store.list_documents()
    return {"documents": docs}
