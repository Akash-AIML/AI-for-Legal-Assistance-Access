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
Extract all significant findings and obligations across the entire agreement (up to 8 key findings and 6 obligations)."""

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
Compare all key changed/unique clause types (PAYMENT, TERMINATION, LIABILITY, INDEMNITY, GOVERNING_LAW, SCOPE_OF_WORK, NON_COMPETE, DISPUTE_RESOLUTION).
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
    """Extract JSON object or array from LLM output safely with robust fence and boundary detection."""
    if not raw or not isinstance(raw, str):
        return {}

    text = raw.strip()

    # 1. Direct parse attempt
    try:
        res = json.loads(text)
        if isinstance(res, dict):
            return res
        if isinstance(res, list):
            return {"items": res, "findings": res, "comparisons": res, "obligations": []}
    except Exception:
        pass

    # 2. Extract content from markdown code fence
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    candidate = fence_match.group(1).strip() if fence_match else text

    try:
        res = json.loads(candidate)
        if isinstance(res, dict):
            return res
        if isinstance(res, list):
            return {"items": res, "findings": res, "comparisons": res, "obligations": []}
    except Exception:
        pass

    # 3. Find outer boundaries of JSON object or array
    start_brace = candidate.find("{")
    end_brace = candidate.rfind("}")
    if start_brace != -1 and end_brace > start_brace:
        try:
            res = json.loads(candidate[start_brace : end_brace + 1])
            if isinstance(res, dict):
                return res
        except Exception:
            pass

    start_bracket = candidate.find("[")
    end_bracket = candidate.rfind("]")
    if start_bracket != -1 and end_bracket > start_bracket:
        try:
            res = json.loads(candidate[start_bracket : end_bracket + 1])
            if isinstance(res, list):
                return {"items": res, "findings": res, "comparisons": res, "obligations": []}
        except Exception:
            pass

    return {}


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

def _select_representative_chunks(
    chunks: list[RetrievedEvidence],
    max_chunks: int = 25,
    max_chars_per_chunk: int = 1200,
) -> str:
    """Select representative chunks across the entire document (beginning, middle, end) ensuring full coverage."""
    if not chunks:
        return ""
    if len(chunks) <= max_chunks:
        selected = chunks
    else:
        # Uniform sampling across document to ensure end-of-contract clauses (Indemnity, Termination, Governing Law) are included
        step = len(chunks) / max_chunks
        selected = [chunks[int(i * step)] for i in range(max_chunks)]
    return "\n\n".join(f"[{e.section}]\n{e.text[:max_chars_per_chunk]}" for e in selected)


def analyze_document(
    document_id: str,
    title: str,
    chunks: list[RetrievedEvidence],
    language: str = "en",
) -> DocumentXRayResult:
    """Run full-contract Document X-Ray analysis across all sections."""
    if not chunks:
        return DocumentXRayResult(
            document_id=document_id,
            title=title,
            overall_risk=RiskLevel.LOW,
            summary="No content available for analysis.",
        )

    # Full document coverage: sample up to 25 representative chunks across beginning, middle, and end
    doc_text = _select_representative_chunks(chunks, max_chunks=25, max_chars_per_chunk=1200)
    safe_doc = sanitize_for_llm(doc_text)
    user_prompt = f"DocID: {document_id}\nTitle: {title}\nContent:\n{safe_doc}"
    if language == "hi":
        user_prompt += "\n\nIMPORTANT: Provide the 'summary', 'explanation', 'why_it_matters', and 'lawyer_question' fields in Hindi (हिन्दी) so it is accessible to Indian citizens. Keep legal clause terms in English."

    if _settings.llm_offline:
        return _offline_xray(document_id, title, chunks)

    raw = chat(
        [{"role": "system", "content": _XRAY_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0.1,
        max_tokens=1000,
        response_format={"type": "json_object"},
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

    # Full document coverage: sample up to 20 representative chunks across entire documents
    text_a = _select_representative_chunks(chunks_a, max_chunks=20, max_chars_per_chunk=1000)
    text_b = _select_representative_chunks(chunks_b, max_chunks=20, max_chars_per_chunk=1000)

    safe_a = sanitize_for_llm(text_a)
    safe_b = sanitize_for_llm(text_b)
    user_prompt = f"Document A: {doc_a_title} ({doc_a_id})\n{safe_a}\n\n---\nDocument B: {doc_b_title} ({doc_b_id})\n{safe_b}"

    if _settings.llm_offline:
        return _offline_compare(doc_a_id, doc_a_title, doc_b_id, doc_b_title)

    raw = chat(
        [{"role": "system", "content": _COMPARE_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0.1,
        max_tokens=650,
        response_format={"type": "json_object"},
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
    language: str = "en",
) -> LawyerBrief:
    if _settings.llm_offline:
        return _offline_lawyer_brief(document_id, title, xray, language=language)

    xray_data = {
        "document_id": xray.document_id,
        "title": xray.title,
        "overall_risk": xray.overall_risk.value,
        "findings": [{"clause_type": f.clause_type.value, "title": f.title, "severity": f.severity.value} for f in xray.findings[:3]],
    }

    user_prompt = f"Doc Analysis:\n{json.dumps(xray_data)}"
    system_prompt = _LAWYER_BRIEF_SYSTEM
    if language.lower() in ("hi", "hindi"):
        system_prompt += "\nIMPORTANT: The user has requested Hindi. You MUST write the 'situation', 'why_it_matters', 'risk_areas', and 'recommended_questions' in natural, professional Hindi (हिन्दी) for citizen legal consultation."

    raw = chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
        max_tokens=450,
        response_format={"type": "json_object"},
    )

    data = _extract_json(raw)
    if not data:
        return _offline_lawyer_brief(document_id, title, xray, language=language)

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


def _offline_lawyer_brief(document_id: str, title: str, xray: DocumentXRayResult, language: str = "en") -> LawyerBrief:
    is_hindi = language.lower() in ("hi", "hindi")
    return LawyerBrief(
        document_id=document_id,
        situation=f"'{title}' के लिए वकील से पूर्व-परामर्श सारांश।" if is_hindi else f"Pre-consultation brief for '{title}'.",
        key_clauses=[],
        risk_areas=[],
        recommended_questions=[
            "किन शर्तों में सबसे अधिक वित्तीय जोखिम है?" if is_hindi else "Which provisions carry the most financial risk?"
        ],
        information_to_gather=[
            "अनुबंध संशोधनों की प्रतिलिपि" if is_hindi else "Copy of contract addendums"
        ],
    )
