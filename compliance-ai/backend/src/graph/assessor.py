"""Evidence Assessment Engine.

Resolves version/authority precedence deterministically (metadata-first), then
classifies the remaining evidence and recommends a decision. This is the
project's core trust layer: no answer is generated until evidence is assessed.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from models import (
    Chunk,
    Decision,
    DocStatus,
    EvidenceStatus,
    RetrievedEvidence,
)

STATUS_RANK = {
    DocStatus.ACTIVE: 0,
    DocStatus.REVIEW_OVERDUE: 1,
    DocStatus.DRAFT: 2,
    DocStatus.SUPERSEDED: 3,
    DocStatus.UNKNOWN: 4,
}
AUTHORITY_RANK = {"official": 0, "standard": 1, "supporting": 2}
# Effective date: newer wins. Missing date treated as oldest.
_EPOCH = date(1970, 1, 1)


def _jurisdiction_match(meta_jurisdiction: str, user_jurisdiction: str) -> int:
    if not user_jurisdiction or user_jurisdiction == "Global":
        return 1
    return 0 if meta_jurisdiction == user_jurisdiction else 2


def _version_tuple(v: str) -> tuple:
    import re

    return tuple(int(x) for x in re.findall(r"\d+", v or "0")) or (0,)


def _tokens(text: str) -> set:
    import re

    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _numbers(text: str) -> set:
    import re

    return {n for n in re.findall(r"\d+", text) if len(n) <= 6 and n != "4"}


def _is_genuine_conflict(a: RetrievedEvidence, b: RetrievedEvidence) -> bool:
    """True when two docs are structurally similar (high overlap) but quote
    different numeric figures — a genuine contradiction rather than complement."""
    ta, tb = _tokens(a.text), _tokens(b.text)
    if not ta or not tb:
        return False
    jaccard = len(ta & tb) / len(ta | tb)
    if jaccard < 0.45:
        return False
    nums_a, nums_b = _numbers(a.text), _numbers(b.text)
    return bool(nums_a) and bool(nums_b) and nums_a != nums_b


class EvidenceAssessment:
    def __init__(self, user_jurisdiction: str = ""):
        self.user_jurisdiction = user_jurisdiction

    def precedence_key(self, m):
        return (
            STATUS_RANK.get(m.metadata.status, 99),
            AUTHORITY_RANK.get(m.metadata.authority, 9),
            _jurisdiction_match(m.metadata.jurisdiction, self.user_jurisdiction),
            m.metadata.effective_date or _EPOCH,
            _version_tuple(m.metadata.version),
        )

    def _resolve_all(self, evidence: list[RetrievedEvidence]) -> list[RetrievedEvidence]:
        """Highest-precedence chunk per document_id, sorted by fusion score.

        When the user's jurisdiction is known, scope-consistent docs (matching
        jurisdiction or Global) are preferred; mismatched regions are dropped
        unless nothing else exists.
        """
        best: dict[str, RetrievedEvidence] = {}
        for ev in evidence:
            doc = ev.metadata.document_id
            if doc not in best or self.precedence_key(ev) < self.precedence_key(best[doc]):
                best[doc] = ev
        resolved = sorted(best.values(), key=lambda e: -e.fusion_score)
        if self.user_jurisdiction and resolved:
            scoped = [
                e
                for e in resolved
                if e.metadata.jurisdiction in ("Global", self.user_jurisdiction)
            ]
            if scoped:
                return scoped
        return resolved

    def resolve_versions(self, evidence: list[RetrievedEvidence]) -> list[RetrievedEvidence]:
        """resolve_versions + relevance gate so weak hits don't drive decisions."""
        resolved = self._resolve_all(evidence)
        if not resolved:
            return resolved
        top = resolved[0].fusion_score
        if top <= 0:
            return resolved
        kept = [e for e in resolved if e.fusion_score >= 0.3 * top]
        return kept or resolved[:1]

    def assess(self, evidence: list[RetrievedEvidence], restricted: bool = False) -> "AssessmentResult":
        # Restricted access takes precedence: if the strongest content for the
        # query is out of the user's reach, refuse clearly instead of answering
        # from weak, unrelated permitted docs.
        if restricted:
            return AssessmentResult(
                evidence=[],
                status=EvidenceStatus.RESTRICTED,
                decision=Decision.ANSWER,
                notes=["The requested content exists but your access level does not permit retrieval."],
                warnings=["Restricted content."],
            )

        resolved = self.resolve_versions(evidence)
        if not resolved:
            return AssessmentResult(
                evidence=[],
                status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                decision=Decision.CLARIFY,
                notes=["No evidence retrieved."],
                warnings=[],
            )

        # --- Conflict: two distinct, same-scope, high-priority docs with high text
        # overlap AND a differing numeric figure (e.g. reimbursement caps). This
        # distinguishes genuine conflicts from complementary policies.
        top = [e for e in resolved if e.metadata.status == DocStatus.ACTIVE]
        official = [e for e in top if e.metadata.authority == "official"]
        conflicts: list[tuple] = []
        for e in official:
            j = e.metadata.jurisdiction
            if j == "Global":
                continue
            for other in official:
                if other.metadata.document_id == e.metadata.document_id:
                    continue
                if other.metadata.jurisdiction != j:
                    continue
                if _is_genuine_conflict(e, other):
                    conflicts.append((j, {e.metadata.document_id, other.metadata.document_id}))
        conflicts = list({tuple(sorted(c[1])): (c[0], c[1]) for c in conflicts}.values())
        if conflicts:
            notes = [
                f"Conflicting guidance from documents {sorted(c[1])} for jurisdiction {c[0]}."
                for c in conflicts
            ]
            return AssessmentResult(
                evidence=resolved,
                status=EvidenceStatus.CONFLICTING_EVIDENCE,
                decision=Decision.ESCALATE,
                notes=notes,
                warnings=notes,
                conflicts=conflicts,
            )

        # --- Outdated / review overdue ---
        stale = [e for e in resolved if e.metadata.status == DocStatus.REVIEW_OVERDUE]
        has_active = any(e.metadata.status == DocStatus.ACTIVE for e in resolved)
        superseded_only = (
            not has_active
            and any(e.metadata.status == DocStatus.SUPERSEDED for e in resolved)
        )

        # --- Jurisdiction ambiguity: user scope unknown, docs split across
        # jurisdictions, the candidates are comparably relevant, and the strongest
        # match is itself jurisdiction-specific (a Global top match is answerable).
        all_resolved = self._resolve_all(evidence)
        top_score = all_resolved[0].fusion_score if all_resolved else 0
        strong = [e for e in all_resolved if top_score > 0 and e.fusion_score >= 0.5 * top_score]
        jurisdictions = {
            e.metadata.jurisdiction
            for e in strong
            if e.metadata.jurisdiction != "Global"
        }
        top_is_global = all_resolved and all_resolved[0].metadata.jurisdiction == "Global"
        if len(jurisdictions) > 1 and not self.user_jurisdiction and not top_is_global:
            return AssessmentResult(
                evidence=resolved,
                status=EvidenceStatus.AMBIGUOUS,
                decision=Decision.CLARIFY,
                notes=[f"Which jurisdiction applies? Candidates: {', '.join(sorted(jurisdictions))}."],
                warnings=["Multiple regional policies matched; scope not specified."],
            )

        if superseded_only:
            notes = [
                "Only superseded versions of the relevant document were found; an active "
                "version may not be indexed."
            ]
            return AssessmentResult(
                evidence=resolved,
                status=EvidenceStatus.OUTDATED_EVIDENCE,
                decision=Decision.ESCALATE,
                notes=notes,
                warnings=notes,
            )

        warnings = []
        if stale:
            for e in stale:
                warnings.append(
                    f"{e.metadata.title} is overdue for review (last reviewed "
                    f"{e.metadata.review_date or 'unknown'})."
                )
        return AssessmentResult(
            evidence=resolved,
            status=EvidenceStatus.SUPPORTED,
            decision=Decision.ANSWER,
            notes=["Evidence is consistent and authoritative."],
            warnings=warnings,
        )


class AssessmentResult:
    def __init__(
        self,
        evidence: list[RetrievedEvidence],
        status: EvidenceStatus,
        decision: Decision,
        notes: list[str],
        warnings: list[str],
        conflicts: Optional[list] = None,
    ):
        self.evidence = evidence
        self.status = status
        self.decision = decision
        self.notes = notes
        self.warnings = warnings
        self.conflicts = conflicts or []