"""Graph nodes: understand -> retrieve -> assess -> decide -> answer/clarify/escalate."""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from config import get_settings
from graph.assessor import EvidenceAssessment
from graph.state import GraphState
from llm import chat
from models import Decision, Escalation, RetrievedEvidence
from retrieval.evidence import detect_restricted, retrieve_evidence, understand_query

_settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_GROUNDED = (
    "You are a legal document analysis assistant. Answer using ONLY the provided "
    "evidence excerpts from the uploaded legal documents. Every factual claim must be "
    "followed by a bracketed citation like [source: <Title>, <Section>, <DocID>]. If "
    "the evidence is insufficient, say so clearly and do not speculate. Do not provide "
    "legal advice — only explain what the documents say and identify issues for review.\n\n"
    "Be thorough: expand on all the relevant points the evidence supports. Rather "
    "than a one-line summary, produce a complete self-contained answer of several "
    "short paragraphs covering who/what applies, the key clause, any conditions or "
    "exceptions, and practical next steps. Keep every claim cited to the evidence."
)



def node_understand(state: GraphState) -> dict:
    t0 = time.time()
    understood = understand_query(state["question"], state["frame"])
    dt = (time.time() - t0) * 1000.0
    logger.debug("Node 'understand' executed in %.1fms", dt)
    return {"understood": understood}


def node_retrieve(state: GraphState) -> dict:
    t0 = time.time()
    evidence = retrieve_evidence(state["question"], state.get("understood", {}), state["frame"])
    restricted = detect_restricted(state["question"], state["frame"])
    dt = (time.time() - t0) * 1000.0
    logger.debug("Node 'retrieve' executed in %.1fms | evidence=%d | restricted=%s", dt, len(evidence), restricted)
    return {"evidence": evidence, "restricted": restricted}


def node_assess(state: GraphState) -> dict:
    t0 = time.time()
    frame = state["frame"]
    assessment = EvidenceAssessment(user_jurisdiction=frame.jurisdiction).assess(
        state.get("evidence", []), restricted=state.get("restricted", False)
    )
    dt = (time.time() - t0) * 1000.0
    logger.debug("Node 'assess' executed in %.1fms | status=%s", dt, assessment.status.value if assessment else "N/A")
    return {"assessment": assessment}


def node_decide(state: GraphState) -> dict:
    t0 = time.time()
    assessment = state["assessment"]
    decision = assessment.decision if assessment else Decision.CLARIFY
    dt = (time.time() - t0) * 1000.0
    logger.debug("Node 'decide' executed in %.1fms | decision=%s", dt, decision.value if hasattr(decision, "value") else decision)
    return {"decision": decision}


def _citations(evidence: list[RetrievedEvidence]) -> list[dict]:
    return [
        {
            "chunk_id": e.chunk_id,
            "title": e.metadata.title,
            "section": e.section,
            "doc_id": e.metadata.document_id,
            "status": e.metadata.status.value,
            "effective_date": e.metadata.effective_date.isoformat()
            if e.metadata.effective_date
            else "",
            "jurisdiction": e.metadata.jurisdiction,
            "version": e.metadata.version,
            "authority": e.metadata.authority,
            "snippet": e.text[:280],
        }
        for e in evidence
    ]


def node_generate(state: GraphState) -> dict:
    t0 = time.time()
    assessment = state["assessment"]
    evidence = assessment.evidence if assessment else []
    if assessment and assessment.status.value == "RESTRICTED":
        return {
            "answer": (
                "I'm unable to retrieve this content. It is restricted and your "
                "current access level (%s) does not permit viewing it. "
                "Contact an HR or Compliance admin if you believe you should have access."
                % state["frame"].role
            ),
            "citations": [],
            "decision": Decision.ANSWER,
        }
    if not evidence:
        return {
            "answer": "I could not find sufficient information in the knowledge base to answer this question.",
            "citations": [],
            "decision": Decision.ANSWER,
        }

    if _settings.llm_offline:
        answer = _offline_answer(state["question"], evidence)
    else:
        context = "\n\n".join(
            f"[{i}] ({e.metadata.title}, {e.section}, {e.metadata.document_id} v{e.metadata.version})\n{e.text}"
            for i, e in enumerate(evidence)
        )
        answer = chat(
            [
                {"role": "system", "content": SYSTEM_GROUNDED},
                {"role": "user", "content": f"Question: {state['question']}\n\nEvidence:\n{context}"},
            ],
            temperature=0.1,
            max_tokens=300,
        )
    dt = (time.time() - t0) * 1000.0
    logger.debug("Node 'generate' executed in %.1fms", dt)
    return {"answer": answer, "citations": _citations(evidence)}


def _offline_answer(question: str, evidence: list[RetrievedEvidence]) -> str:
    top = evidence[0]
    lines = [
        "Based on the available organizational documents:",
        "",
        top.text,
        "",
        "Source: "
        f"{top.metadata.title} (v{top.metadata.version}) — {top.section} [{top.metadata.document_id}]",
    ]
    return "\n".join(lines)


def node_clarify(state: GraphState) -> dict:
    assessment = state["assessment"]
    notes = assessment.notes if assessment else []
    question = notes[0] if notes else "Could you clarify your question?"
    return {
        "clarification": question,
        "answer": "",
        "decision": Decision.CLARIFY,
    }


def node_escalate(state: GraphState) -> dict:
    assessment = state["assessment"]
    escal = Escalation(
        escalation_id=f"ESC-{uuid.uuid4().hex[:6].upper()}",
        user_id=state["frame"].user_id,
        question=state["question"],
        summary="; ".join(assessment.notes if assessment else []),
        reason=assessment.status.value if assessment else "UNKNOWN",
        docs_ids=list({e.metadata.document_id for e in state.get("evidence", [])}),
        passages=[e.text[:300] for e in state.get("evidence", [])][:3],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    msg = (
        f"Human review requested ({escal.escalation_id}). "
        f"Reason: {escal.reason}. {escal.summary}"
    )
    return {
        "escalation": escal,
        "answer": msg,
        "decision": Decision.ESCALATE,
    }


def node_retrieve_more(state: GraphState) -> dict:
    """One additional, broadened retrieval attempt (bounded: no infinite loops)."""
    retries = state.get("retries", 0)
    question = state["question"]
    # broaden by adding the extracted topic to the query for better recall
    topic = state.get("understood", {}).get("topic", "")
    query = f"{question} {topic}".strip()
    evidence = retrieve_evidence(query, state.get("understood", {}), state["frame"])
    return {"evidence": evidence, "retries": retries + 1}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_assess(state: GraphState) -> str:
    decision = state.get("decision", Decision.CLARIFY)
    if decision == Decision.ANSWER:
        return "generate"
    if decision == Decision.CLARIFY:
        return "clarify"
    if decision == Decision.ESCALATE:
        return "escalate"
    if decision == Decision.RETRIEVE_MORE:
        return "retrieve_more"
    return "clarify"


def route_after_retrieve_more(state: GraphState) -> str:
    # After the second attempt: answer if resolved, otherwise escalate.
    if state.get("decision") == Decision.ANSWER:
        return "generate"
    if state.get("decision") == Decision.CLARIFY:
        return "clarify"
    return "escalate"