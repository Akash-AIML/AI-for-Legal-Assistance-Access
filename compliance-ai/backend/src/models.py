"""Shared domain models for documents, chunks, evidence, escalations, and legal analysis."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Existing enums (preserved)
# ---------------------------------------------------------------------------

class DocStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVIEW_OVERDUE = "REVIEW_OVERDUE"
    DRAFT = "DRAFT"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    OUTDATED_EVIDENCE = "OUTDATED_EVIDENCE"
    RESTRICTED = "RESTRICTED"


class Decision(str, Enum):
    ANSWER = "ANSWER"
    CLARIFY = "CLARIFY"
    RETRIEVE_MORE = "RETRIEVE_MORE"
    ESCALATE = "ESCALATE"


# ---------------------------------------------------------------------------
# Legal domain enums (new)
# ---------------------------------------------------------------------------

class AuthorityType(str, Enum):
    """Legal authority hierarchy (highest → lowest)."""
    LAW = "LAW"
    REGULATION = "REGULATION"
    COURT_DECISION = "COURT_DECISION"
    GOVERNMENT_NOTIFICATION = "GOVERNMENT_NOTIFICATION"
    CONTRACT = "CONTRACT"
    COMPANY_POLICY = "COMPANY_POLICY"
    GUIDANCE = "GUIDANCE"
    USER_DOCUMENT = "USER_DOCUMENT"


class ClauseType(str, Enum):
    """Standard legal clause taxonomy."""
    TERMINATION = "TERMINATION"
    PAYMENT = "PAYMENT"
    LIABILITY = "LIABILITY"
    INDEMNITY = "INDEMNITY"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    IP_ASSIGNMENT = "IP_ASSIGNMENT"
    NON_COMPETE = "NON_COMPETE"
    NON_SOLICITATION = "NON_SOLICITATION"
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"
    GOVERNING_LAW = "GOVERNING_LAW"
    RENEWAL = "RENEWAL"
    WARRANTY = "WARRANTY"
    PRIVACY_DATA = "PRIVACY_DATA"
    SCOPE_OF_WORK = "SCOPE_OF_WORK"
    DATA_PROCESSING = "DATA_PROCESSING"
    OTHER = "OTHER"


class RiskLevel(str, Enum):
    """Risk severity for findings."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------------------------------------------------------------------------
# Extended document metadata (new fields added to DocMetadata)
# ---------------------------------------------------------------------------

class DocMetadata(BaseModel):
    """Canonical document-level metadata attached to every chunk."""

    document_id: str = ""
    title: str = ""
    document_type: str = "POLICY"  # POLICY | SOP | HR | LEGAL | MANUAL | CONTRACT | NDA | AGREEMENT
    department: str = "General"
    jurisdiction: str = "Global"
    version: str = "1"
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: DocStatus = DocStatus.ACTIVE
    authority: str = "standard"  # official | standard | supporting
    authority_type: AuthorityType = AuthorityType.USER_DOCUMENT
    governing_law: str = ""  # e.g. "Indian Contract Act, 1872"
    country: str = ""  # e.g. "IN", "US", "DE"
    state: str = ""  # e.g. "Maharashtra"
    citation: str = ""  # e.g. "Section 14, Indian Contract Act"
    source_path: str = ""
    owner: str = "global"
    access_roles: list[str] = Field(default_factory=lambda: ["Employee"])
    tags: list[str] = Field(default_factory=list)


class Chunk(BaseModel):
    """A single retrievable unit of a document."""

    chunk_id: str
    doc_id: str
    section: str
    index: int
    text: str
    metadata: DocMetadata


class RetrievedEvidence(BaseModel):
    """One retrieved + ranked chunk with its retrieval scores."""

    chunk_id: str
    doc_id: str
    section: str
    text: str
    metadata: DocMetadata
    dense_score: float = 0.0
    bm25_score: float = 0.0
    fusion_score: float = 0.0
    relevance: float = 0.0  # 0..1


class ConversationFrame(BaseModel):
    """User context merged with structured conversation state."""

    user_id: str = "anonymous"
    role: str = "Employee"
    department: str = ""
    jurisdiction: str = ""
    session_id: str = ""
    topic: str = ""
    employee_type: str = ""


# Role hierarchy for document access. A user's effective privileges are the
# union of their own role's set plus everything below it (higher roles inherit
# access to content intended for lower roles).
ROLE_PRIVILEGES: dict[str, set[str]] = {
    "Employee": {"Employee"},
    "HR": {"Employee", "HR"},
    "Compliance": {"Employee", "Compliance"},
    "Admin": {"Employee", "HR", "Compliance", "Admin"},
}


def role_privileges(roles: list[str] | None) -> set[str]:
    """Expand a list of user roles into every privilege they hold."""
    out: set[str] = set()
    for r in roles or ():
        out |= ROLE_PRIVILEGES.get(r, {r})
    return out


class Escalation(BaseModel):
    escalation_id: str
    user_id: str
    question: str
    summary: str = ""
    reason: str
    docs_ids: list[str] = Field(default_factory=list)
    passages: list[str] = Field(default_factory=list)
    created_at: str = ""
    status: str = "OPEN"  # OPEN | RESOLVED
    resolution: str = ""


# ---------------------------------------------------------------------------
# Legal analysis models (new)
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    """A single risk finding from document X-Ray analysis."""
    clause_type: ClauseType
    severity: RiskLevel
    section: str  # e.g. "§14.1" or "Section 3.2"
    title: str  # e.g. "Broad IP Assignment"
    explanation: str  # plain-English, 2-3 sentences
    source_text: str  # original clause text
    why_it_matters: str  # practical implication
    lawyer_question: str  # specific question to ask a lawyer


class Obligation(BaseModel):
    """A structured obligation extracted from a legal document."""
    subject: str  # "Employee", "Employer", "Party A"
    action: str  # "Provide written notice"
    deadline: str  # "90 days before termination"
    condition: str  # "If employee wants to terminate"
    source_section: str  # "§14.1"
    consequence: str  # "Contractual requirements apply"


class DocumentXRayResult(BaseModel):
    """Full X-Ray analysis result for a single document."""
    document_id: str
    title: str
    overall_risk: RiskLevel
    summary: str  # 3-5 sentence plain-English summary
    findings: list[Finding] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    lawyer_questions: list[str] = Field(default_factory=list)


class ClauseComparison(BaseModel):
    """A single clause-level comparison between two documents."""
    clause_type: ClauseType
    document_a_text: str
    document_b_text: str
    status: str  # "SAME", "CHANGED", "ADDED", "REMOVED"
    impact: str  # plain-English explanation of why the change matters


class CompareResult(BaseModel):
    """Full comparison result between two documents."""
    document_a_id: str
    document_b_id: str
    document_a_title: str = ""
    document_b_title: str = ""
    comparisons: list[ClauseComparison] = Field(default_factory=list)
    summary: str


class LawyerBrief(BaseModel):
    """Structured pre-consultation brief for a lawyer."""
    document_id: str
    situation: str  # "Employment contract received on 15 Sep 2026..."
    key_clauses: list[dict] = Field(default_factory=list)  # [{section, clause_type, why_it_matters}]
    risk_areas: list[dict] = Field(default_factory=list)  # [{severity, description, source}]
    recommended_questions: list[str] = Field(default_factory=list)
    information_to_gather: list[str] = Field(default_factory=list)