"""Assemble ranked evidence from hybrid retrieval into structured chunks."""
from __future__ import annotations

from typing import Optional

from config import get_settings
from ingestion import store
from llm import chat
from models import Chunk, RetrievedEvidence, role_privileges

_settings = get_settings()

# Ask the LLM to extract structured retrieval context (offline mode falls back to a stub).
_UNDERSTAND_SYSTEM = (
    "You extract structured search context from a user question about company policy.\n"
    "Return ONLY valid JSON with these optional keys: "
    "topic, action, jurisdiction, department, employee_type.\n"
    'Example: {"topic": "annual leave", "action": "carry forward", "jurisdiction": null}'
)


def understand_query(question: str, frame) -> dict:
    """Extract structured context instantly using zero-latency rule parsing."""
    parsed = _rule_parse(question)
    merged = {
        "topic": frame.topic or parsed.get("topic", ""),
        "action": parsed.get("action", ""),
        "jurisdiction": frame.jurisdiction or parsed.get("jurisdiction", ""),
        "department": frame.department or parsed.get("department", ""),
        "employee_type": frame.employee_type or parsed.get("employee_type", ""),
        "question": question,
    }
    return merged


def retrieve_evidence(question: str, understood: dict, frame) -> list[RetrievedEvidence]:
    """Run hybrid retrieval, build evidence objects with scores + metadata."""
    roles = [frame.role] if frame.role else None
    hits = store.hybrid_search(question, allowed_roles=roles)
    evidence: list[RetrievedEvidence] = []
    for cid, fusion in hits:
        meta_flat = store.get_meta(cid)
        if not meta_flat:
            continue
        text = store.get_chunk_text(cid) or ""
        evidence.append(
            RetrievedEvidence(
                chunk_id=cid,
                doc_id=meta_flat.get("document_id", ""),
                section=meta_flat.get("section", "Body"),
                text=text,
                metadata=_flat_to_meta(meta_flat),
                fusion_score=fusion,
            )
        )
    return evidence


def detect_restricted(question: str, frame) -> bool:
    """True when the best reachable content for a query is restricted to the user.

    Compares the strongest restricted hit against the strongest permitted hit in
    the unfiltered ranking: if a restricted doc ties or outscores everything the
    user's role may access, the correct action is a clear refusal.
    """
    user_roles = set([frame.role] if frame.role else [])
    user_privs = role_privileges(list(user_roles))
    hits = store.hybrid_search(question, allowed_roles=None)
    if not hits:
        return False

    def allowed(cid):
        meta = store.get_meta(cid) or {}
        roles = {r.strip() for r in (meta.get("access_roles", "") or "").split(",") if r.strip()}
        return not roles or bool(roles & user_privs)

    permitted = [s for cid, s in hits if allowed(cid)]
    restricted = [s for cid, s in hits if not allowed(cid)]
    if not restricted:
        return False
    if not permitted:
        return True
    return max(restricted) >= max(permitted)


def _flat_to_meta(flat: dict):
    from models import DocMetadata, DocStatus

    m = DocMetadata(
        document_id=flat.get("document_id", ""),
        title=flat.get("title", ""),
        document_type=flat.get("document_type", "POLICY"),
        department=flat.get("department", "General"),
        jurisdiction=flat.get("jurisdiction", "Global"),
        version=flat.get("version", "1"),
        status=DocStatus(flat.get("status", "UNKNOWN")),
        authority=flat.get("authority", "standard"),
        source_path=flat.get("source_path", ""),
        access_roles=[r for r in (flat.get("access_roles", "") or "").split(",") if r],
        tags=[t for t in (flat.get("tags", "") or "").split(",") if t],
    )
    from datetime import date

    try:
        if flat.get("effective_date"):
            m.effective_date = date.fromisoformat(flat["effective_date"])
        if flat.get("review_date"):
            m.review_date = date.fromisoformat(flat["review_date"])
    except ValueError:
        pass
    return m


def _rule_parse(question: str) -> dict:
    """Deterministic offline extractor (keyword-based, no LLM)."""
    q = question.lower()
    out: dict = {"topic": "", "action": "", "jurisdiction": "", "department": "", "employee_type": ""}
    topics = {
        "leave": "annual leave",
        "annual leave": "annual leave",
        "vacation": "annual leave",
        "carry": "annual leave",
        "maternity": "maternity leave",
        "expense": "expense reimbursement",
        "reimbursement": "expense reimbursement",
        "hotel": "expense reimbursement",
        "vpn": "remote access",
        "password": "access control",
        "iso 27001": "access control",
        "sox": "records retention",
        "records": "records retention",
        "gdpr": "data protection",
        "compensation": "compensation",
        "bonus": "compensation",
        "executive": "compensation",
    }
    for key, topic in topics.items():
        if key in q:
            out["topic"] = topic
            break
    if "carry" in q or "carry forward" in q or "roll over" in q:
        out["action"] = "carry forward"
    for j in ["india", "in "]:
        if j in q and out["jurisdiction"] == "":
            out["jurisdiction"] = "IN"
            break
    if "germany" in q or "de " in q:
        out["jurisdiction"] = "DE"
    if "contract" in q or "contractor" in q or "fixed-term" in q:
        out["employee_type"] = "contract"
    elif "permanent" in q:
        out["employee_type"] = "permanent"
    return out


def _parse_json(raw: str) -> dict:
    import json
    import re

    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}