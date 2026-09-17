"""Legal Intelligence Engine — Document X-Ray, Comparison, and Lawyer Brief.

Optimized for ultra-fast response latency and structured legal intelligence.
"""
from __future__ import annotations

import json
import re
from typing import Any

from config import get_settings
from ingestion.safety import sanitize_for_llm
from llm import chat
from models import (
    ClauseComparison,
    ClauseType,
    CompareResult,
    DocumentXRayResult,
    Finding,
    LawyerBrief,
    Obligation,
    RiskLevel,
    RetrievedEvidence,
)

_settings = get_settings()

# ---------------------------------------------------------------------------
# Concise System Prompts
# ---------------------------------------------------------------------------

_XRAY_SYSTEM = """You are a legal document X-Ray AI. Return ONLY a single raw valid JSON object (no markdown, no extra text).
Structure:
{
  "summary": "2 sentence document summary.",
  "overall_risk": "HIGH" | "MEDIUM" | "LOW",
  "findings": [
    {
      "clause_type": "TERMINATION",
      "severity": "HIGH",
      "section": "§8.2",
      "title": "Short Title",
      "explanation": "1-2 sentences explaining what the clause says.",
      "source_text": "Key excerpt",
      "why_it_matters": "Practical implication.",
      "lawyer_question": "1 specific question for a lawyer."
    }
  ],
  "obligations": [
    {
      "subject": "Tenant",
      "action": "Pay rent",
      "deadline": "1st of month",
      "condition": "Monthly",
      "source_section": "§3.1"
    }
  ]
}
Extract max 3 critical findings and max 2 obligations."""

_COMPARE_SYSTEM = """You are a legal contract comparison AI. Return ONLY a single raw valid JSON object (no markdown, no extra text).
Structure:
{
  "summary": "2 sentence high-level comparison summary.",
  "comparisons": [
    {
      "clause_type": "PAYMENT",
      "document_a_text": "Excerpt from Doc A",
      "document_b_text": "Excerpt from Doc B",
      "status": "CHANGED",
      "impact": "1-2 sentence practical impact explanation."
    }
  ]
}
Compare max 4-5 key changed/unique clause types (PAYMENT, TERMINATION, LIABILITY, INDEMNITY, GOVERNING_LAW, SCOPE_OF_WORK).
Status must be: CHANGED, SAME, ADDED, REMOVED."""

_LAWYER_BRIEF_SYSTEM = """You are a legal consultation assistant. Return ONLY a single raw valid JSON object:
{
  "situation": "2 sentence situation summary.",
  "key_clauses": [{"section": "§3.1", "clause_type": "PAYMENT", "why_it_matters": "Implication"}],
  "risk_areas": [{"severity": "HIGH", "description": "Risk description", "source": "§3.1"}],
  "recommended_questions": ["Question 1", "Question 2", "Question 3"],
  "information_to_gather": ["Item 1", "Item 2"]
}"""

# ---------------------------------------------------------------------------
# Structured Output & Type Parsing
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> dict:
    """Extract JSON object from LLM output safely with auto-repair for truncated JSON."""
    res = None
    try:
        res = json.loads(raw)
    except Exception:
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
        candidate = match.group(1) if match else raw
        match_obj = re.search(r"[\{\[].*", candidate, re.DOTALL)
        if match_obj:
            snippet = match_obj.group(0).strip()
            # Auto-repair trailing truncated JSON by trying bracket completions
            for suffix in ["", "}", "]}", "\"]}", "\"}]}", "}\n]}", "\"\n}\n]}"]:
                try:
                    res = json.loads(snippet + suffix)
                    break
                except Exception:
                    pass

    if isinstance(res, list):
        return {"items": res, "findings": res, "comparisons": res, "obligations": []}
    return res if isinstance(res, dict) else {}


def _parse_clause_type(s: str) -> ClauseType:
    try:
        return ClauseType(s.upper().replace(" ", "_"))
    except Exception:
        return ClauseType.OTHER


def _parse_risk_level(s: str) -> RiskLevel:
    try:
        return RiskLevel(s.upper())
    except Exception:
        return RiskLevel.MEDIUM


# ---------------------------------------------------------------------------
# Fast Document X-Ray Analysis
# ---------------------------------------------------------------------------

def analyze_document(
    document_id: str,
    title: str,
    chunks: list[RetrievedEvidence],
) -> DocumentXRayResult:
    if not chunks:
        return DocumentXRayResult(
            document_id=document_id,
            title=title,
            overall_risk=RiskLevel.LOW,
            summary="No content available for analysis.",
        )

    # Truncate to top 5 chunks for fast < 8s inference
    doc_text = "\n\n".join(f"[{e.section}]\n{e.text[:400]}" for e in chunks[:5])
    safe_doc = sanitize_for_llm(doc_text)
    user_prompt = f"DocID: {document_id}\nTitle: {title}\nContent:\n{safe_doc}"

    if _settings.llm_offline:
        return _offline_xray(document_id, title, chunks)

    raw = chat(
        [{"role": "system", "content": _XRAY_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0.1,
        max_tokens=600,
    )

    data = _extract_json(raw)
    if not data:
        return _offline_xray(document_id, title, chunks)

    findings = [
        Finding(
            clause_type=_parse_clause_type(f.get("clause_type", "OTHER")),
            severity=_parse_risk_level(f.get("severity", "MEDIUM")),
            section=str(f.get("section", "")),
            title=str(f.get("title", "")),
            explanation=str(f.get("explanation", "")),
            source_text=str(f.get("source_text", "")),
            why_it_matters=str(f.get("why_it_matters", "")),
            lawyer_question=str(f.get("lawyer_question", "")),
        )
        for f in data.get("findings", []) if isinstance(f, dict)
    ]

    obligations = [
        Obligation(
            subject=str(o.get("subject", "")),
            action=str(o.get("action", "")),
            deadline=str(o.get("deadline", "")),
            condition=str(o.get("condition", "")),
            source_section=str(o.get("source_section", "")),
            consequence=str(o.get("consequence", "")),
        )
        for o in data.get("obligations", []) if isinstance(o, dict)
    ]

    return DocumentXRayResult(
        document_id=document_id,
        title=title,
        overall_risk=_parse_risk_level(str(data.get("overall_risk", "MEDIUM"))),
        summary=str(data.get("summary", "")),
        findings=findings,
        obligations=obligations,
        lawyer_questions=data.get("lawyer_questions", []),
    )


# ---------------------------------------------------------------------------
# Fast Contract Comparison
# ---------------------------------------------------------------------------

def compare_documents(
    doc_a_id: str,
    doc_a_title: str,
    chunks_a: list[RetrievedEvidence],
    doc_b_id: str,
    doc_b_title: str,
    chunks_b: list[RetrievedEvidence],
) -> CompareResult:
    if not chunks_a and not chunks_b:
        return CompareResult(
            document_a_id=doc_a_id,
            document_b_id=doc_b_id,
            document_a_title=doc_a_title,
            document_b_title=doc_b_title,
            summary="No content available for comparison.",
        )

    # Truncate to top 5 key chunks per document for fast comparison
    text_a = "\n\n".join(f"[{e.section}]\n{e.text[:400]}" for e in chunks_a[:5])
    text_b = "\n\n".join(f"[{e.section}]\n{e.text[:400]}" for e in chunks_b[:5])

    safe_a = sanitize_for_llm(text_a)
    safe_b = sanitize_for_llm(text_b)
    user_prompt = f"Document A: {doc_a_title} ({doc_a_id})\n{safe_a}\n\n---\nDocument B: {doc_b_title} ({doc_b_id})\n{safe_b}"

    if _settings.llm_offline:
        return _offline_compare(doc_a_id, doc_a_title, doc_b_id, doc_b_title)

    raw = chat(
        [{"role": "system", "content": _COMPARE_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0.1,
        max_tokens=650,
    )

    data = _extract_json(raw)
    if not data:
        return _offline_compare(doc_a_id, doc_a_title, doc_b_id, doc_b_title)

    comparisons = []
    comp_list = data.get("comparisons", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    for c in comp_list:
        if isinstance(c, dict):
            doc_a_txt = c.get("document_a_text") or c.get("doc_a_text") or c.get("text_a") or ""
            doc_b_txt = c.get("document_b_text") or c.get("doc_b_text") or c.get("text_b") or ""
            clause_raw = c.get("clause_type") or c.get("clause") or c.get("type") or "OTHER"
            impact_txt = c.get("impact") or c.get("why_it_matters") or c.get("explanation") or ""
            comparisons.append(
                ClauseComparison(
                    clause_type=_parse_clause_type(str(clause_raw)),
                    document_a_text=str(doc_a_txt),
                    document_b_text=str(doc_b_txt),
                    status=str(c.get("status", "SAME")).upper(),
                    impact=str(impact_txt),
                )
            )

    return CompareResult(
        document_a_id=doc_a_id,
        document_b_id=doc_b_id,
        document_a_title=doc_a_title,
        document_b_title=doc_b_title,
        comparisons=comparisons,
        summary=str(data.get("summary", "")),
    )


# ---------------------------------------------------------------------------
# Fast Lawyer Brief Generation
# ---------------------------------------------------------------------------

def generate_lawyer_brief(
    document_id: str,
    title: str,
    xray: DocumentXRayResult,
) -> LawyerBrief:
    if _settings.llm_offline:
        return _offline_lawyer_brief(document_id, title, xray)

    xray_data = {
        "document_id": xray.document_id,
        "title": xray.title,
        "overall_risk": xray.overall_risk.value,
        "findings": [{"clause_type": f.clause_type.value, "title": f.title, "severity": f.severity.value} for f in xray.findings[:3]],
    }

    user_prompt = f"Doc Analysis:\n{json.dumps(xray_data)}"
    raw = chat(
        [{"role": "system", "content": _LAWYER_BRIEF_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
        max_tokens=350,
    )

    data = _extract_json(raw)
    if not data:
        return _offline_lawyer_brief(document_id, title, xray)

    return LawyerBrief(
        document_id=document_id,
        situation=str(data.get("situation", f"Document {title} requires legal review.")),
        key_clauses=data.get("key_clauses", []),
        risk_areas=data.get("risk_areas", []),
        recommended_questions=data.get("recommended_questions", []),
        information_to_gather=data.get("information_to_gather", []),
    )


# ---------------------------------------------------------------------------
# Offline Fallbacks (Demo Mode)
# ---------------------------------------------------------------------------

def _offline_xray(document_id: str, title: str, chunks: list[RetrievedEvidence]) -> DocumentXRayResult:
    return DocumentXRayResult(
        document_id=document_id,
        title=title,
        overall_risk=RiskLevel.MEDIUM,
        summary=f"Offline demo analysis of {title}.",
        findings=[
            Finding(
                clause_type=ClauseType.TERMINATION,
                severity=RiskLevel.MEDIUM,
                section="§8.2",
                title="Termination Clause",
                explanation="Standard termination terms apply.",
                source_text="90 days written notice.",
                why_it_matters="Governs contract exit terms.",
                lawyer_question="Are termination terms standard?",
            )
        ],
        obligations=[],
        lawyer_questions=["Are the terms negotiable?"],
    )


def _offline_compare(doc_a_id: str, doc_a_title: str, doc_b_id: str, doc_b_title: str) -> CompareResult:
    return CompareResult(
        document_a_id=doc_a_id,
        document_b_id=doc_b_id,
        document_a_title=doc_a_title,
        document_b_title=doc_b_title,
        comparisons=[
            ClauseComparison(
                clause_type=ClauseType.TERMINATION,
                document_a_text="90 days notice",
                document_b_text="30 days notice",
                status="CHANGED",
                impact="Notice period reduced.",
            )
        ],
        summary="Offline demo contract comparison completed.",
    )


def _offline_lawyer_brief(document_id: str, title: str, xray: DocumentXRayResult) -> LawyerBrief:
    return LawyerBrief(
        document_id=document_id,
        situation=f"Pre-consultation brief for '{title}'.",
        key_clauses=[],
        risk_areas=[],
        recommended_questions=["Which provisions carry the most financial risk?"],
        information_to_gather=["Copy of contract addendums"],
    )
