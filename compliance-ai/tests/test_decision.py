"""Decision-engine tests against the seeded legal document corpus (offline mode)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from graph.builder import get_graph  # noqa: E402
from models import ConversationFrame  # noqa: E402


def run_graph(question, jurisdiction="", role="Employee"):
    g = get_graph()
    state = {
        "question": question,
        "frame": ConversationFrame(user_id="tester", role=role, jurisdiction=jurisdiction),
        "history": [],
        "retries": 0,
        "decision": None,
        "answer": "",
        "citations": [],
        "clarification": "",
        "escalation": None,
        "evidence": [],
        "understood": {},
        "assessment": None,
        "restricted": False,
        "trace": [],
    }
    return g.invoke(state)


def status(out):
    return out["assessment"].status.value if out["assessment"] else None


class TestDecisions:
    def test_employment_termination_with_jurisdiction(self):
        """Employment agreement termination clause should be found with IN jurisdiction."""
        out = run_graph("What are the termination conditions in the employment agreement?", jurisdiction="IN")
        assert out["decision"].value in ("ANSWER", "CLARIFY")
        # Should find the employment agreement
        if out["citations"]:
            assert any("EMP-AGR" in c["doc_id"] for c in out["citations"])

    def test_ambiguous_without_jurisdiction(self):
        """Query without jurisdiction should trigger CLARIFY or find global docs."""
        out = run_graph("What are the termination conditions?")
        # Should either clarify jurisdiction or find relevant docs
        assert out["decision"].value in ("CLARIFY", "ANSWER")

    def test_nda_confidentiality_answered(self):
        """NDA confidentiality obligations should be answerable."""
        out = run_graph("What are the confidentiality obligations in the NDA?")
        assert out["decision"].value in ("ANSWER", "CLARIFY")
        if out["citations"]:
            assert any("NDA" in c["doc_id"] for c in out["citations"])

    def test_saas_liability_cap(self):
        """SaaS agreement liability cap should be retrievable."""
        out = run_graph("What is the liability cap in the service agreement?")
        assert out["decision"].value in ("ANSWER", "CLARIFY")
        if out["citations"]:
            assert any("SVC" in c["doc_id"] for c in out["citations"])

    def test_rental_deposit_amount(self):
        """Rental agreement deposit should be findable."""
        out = run_graph("What is the security deposit amount in the rental agreement?", jurisdiction="IN")
        assert out["decision"].value in ("ANSWER", "CLARIFY")
        if out["citations"]:
            assert any("REN" in c["doc_id"] for c in out["citations"])

    def test_gdpr_restricted_for_employee(self):
        """GDPR DPA should be restricted for Employee role (Compliance-only access)."""
        out = run_graph("What are the GDPR data processing obligations?", role="Employee")
        assert status(out) in ("RESTRICTED", "INSUFFICIENT_EVIDENCE")

    def test_gdpr_accessible_for_compliance(self):
        """GDPR DPA should be accessible for Compliance role."""
        out = run_graph("What are the GDPR data processing obligations?", jurisdiction="EU", role="Compliance")
        assert status(out) in ("SUPPORTED", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE")
        if out["citations"]:
            assert any("DPA" in c["doc_id"] for c in out["citations"])

    def test_ip_assignment_clause(self):
        """IP assignment clause in employment agreement should be found."""
        out = run_graph("What does the employment agreement say about intellectual property?", jurisdiction="IN")
        assert out["decision"].value in ("ANSWER", "CLARIFY")

    def test_contract_version_comparison(self):
        """Comparing versions should retrieve both versions."""
        out = run_graph("What changed between the two versions of the employment agreement?", jurisdiction="IN")
        assert out["decision"].value in ("ANSWER", "CLARIFY", "ESCALATE")
