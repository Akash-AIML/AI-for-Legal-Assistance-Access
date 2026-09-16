"""LangGraph state schema."""
from __future__ import annotations

from typing import TypedDict

from graph.assessor import AssessmentResult
from models import ConversationFrame, Decision, Escalation, RetrievedEvidence


class GraphState(TypedDict):
    question: str
    frame: ConversationFrame
    history: list[dict]  # recent user/assistant messages
    understood: dict
    evidence: list[RetrievedEvidence]
    assessment: AssessmentResult | None
    decision: Decision
    answer: str
    citations: list[dict]
    clarification: str
    escalation: Escalation | None
    retries: int
    restricted: bool
    trace: list[dict]  # audit log of decision steps