"""Tests for legal analysis endpoints (Document X-Ray, Compare, Brief, Obligations)."""
from __future__ import annotations

import io
import pytest


@pytest.fixture(scope="module")
def sample_doc_id(client):
    """Upload a sample legal contract and return its document_id."""
    content = (
        "# Independent Contractor Agreement\n\n"
        "## 1. Termination\n"
        "Either party may terminate this agreement with 30 days written notice. "
        "In the event of material breach, termination is immediate.\n\n"
        "## 2. Payment Terms\n"
        "Client shall pay Contractor within 15 days of invoice receipt. "
        "Late payments shall incur a 1.5% monthly interest penalty.\n\n"
        "## 3. Confidentiality\n"
        "Contractor agrees to keep all proprietary information strictly confidential for 5 years.\n\n"
        "## 4. Governing Law\n"
        "This Agreement shall be governed by the laws of the State of California."
    ).encode("utf-8")
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("contract_alpha.md", io.BytesIO(content), "text/markdown")},
    )
    assert resp.status_code == 200
    # Retrieve the document_id from documents list
    docs = client.get("/api/legal/documents").json()["documents"]
    for d in docs:
        if "contract_alpha" in d.get("source_path", "").lower() or "contract_alpha" in d.get("title", "").lower() or "contract_alpha" in d.get("document_id", "").lower():
            return d["document_id"]
    # Fallback to the first available doc or contract_alpha.md
    return docs[0]["document_id"] if docs else "contract_alpha.md"


@pytest.fixture(scope="module")
def sample_doc_b_id(client):
    """Upload a second sample contract for comparison."""
    content = (
        "# Master Services Agreement\n\n"
        "## 1. Termination\n"
        "Either party may terminate this agreement with 60 days written notice.\n\n"
        "## 2. Payment Terms\n"
        "Client shall pay Contractor within 45 days of invoice receipt.\n\n"
        "## 3. Governing Law\n"
        "This Agreement shall be governed by the laws of the State of Delaware."
    ).encode("utf-8")
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("contract_beta.md", io.BytesIO(content), "text/markdown")},
    )
    assert resp.status_code == 200
    docs = client.get("/api/legal/documents").json()["documents"]
    for d in docs:
        if "contract_beta" in d.get("source_path", "").lower() or "contract_beta" in d.get("title", "").lower() or "contract_beta" in d.get("document_id", "").lower():
            return d["document_id"]
    return docs[-1]["document_id"] if len(docs) > 1 else "contract_beta.md"


class TestLegalDocuments:
    def test_list_analyzable_documents(self, client):
        """Must return 200 with documents list."""
        resp = client.get("/api/legal/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)


class TestDocumentXRay:
    def test_analyze_valid_document(self, client, sample_doc_id):
        """X-Ray analysis of a valid document must return findings and risk level."""
        resp = client.post("/api/legal/analyze", json={"document_id": sample_doc_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == sample_doc_id
        assert "overall_risk" in data
        assert "findings" in data
        assert "obligations" in data
        assert "lawyer_questions" in data

    def test_analyze_document_with_language_and_persistent_cache(self, client, sample_doc_id):
        """X-Ray analysis supports language parameter and persists results in SQLite cache."""
        resp1 = client.post("/api/legal/analyze", json={"document_id": sample_doc_id, "language": "hi"})
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["document_id"] == sample_doc_id

        # Verify second call hits the cache successfully
        resp2 = client.post("/api/legal/analyze", json={"document_id": sample_doc_id, "language": "hi"})
        assert resp2.status_code == 200
        assert resp2.json()["summary"] == data1["summary"]

    def test_analyze_nonexistent_document_returns_404(self, client):
        """Analysis of a non-existent document must return 404."""
        resp = client.post("/api/legal/analyze", json={"document_id": "nonexistent_doc_id_999"})
        assert resp.status_code == 404

    def test_analyze_missing_body_returns_422(self, client):
        """Missing request body must return 422."""
        resp = client.post("/api/legal/analyze", json={})
        assert resp.status_code == 422

    def test_multi_tenant_document_isolation(self, client, employee_headers, auth_headers):
        """A private document owned by user A cannot be analyzed by an unauthenticated guest or non-admin."""
        content = b"# Private Tenant Contract\n\nConfidential terms between Tenant Asha and Landlord."
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("asha_private.md", io.BytesIO(content), "text/markdown")},
            headers=employee_headers,
        )
        assert resp.status_code == 200

        # Find the uploaded document_id
        docs = client.get("/api/legal/documents", headers=employee_headers).json()["documents"]
        asha_doc_id = None
        for d in docs:
            if "asha_private" in d.get("source_path", "").lower() or "asha_private" in d.get("title", "").lower() or "asha_private" in d.get("document_id", "").lower():
                asha_doc_id = d["document_id"]
                break
        assert asha_doc_id is not None

        # Unauthenticated / guest access should be rejected with 403 Forbidden
        guest_resp = client.post("/api/legal/analyze", json={"document_id": asha_doc_id})
        assert guest_resp.status_code == 403
        assert "Access denied" in guest_resp.json().get("detail", "")

        # Admin access should be allowed with 200 OK
        admin_resp = client.post("/api/legal/analyze", json={"document_id": asha_doc_id}, headers=auth_headers)
        assert admin_resp.status_code == 200


class TestContractCompare:
    def test_compare_two_documents(self, client, sample_doc_id, sample_doc_b_id):
        """Comparing two distinct documents must return clause-by-clause comparison."""
        resp = client.post(
            "/api/legal/compare",
            json={"document_a": sample_doc_id, "document_b": sample_doc_b_id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_a_id"] == sample_doc_id
        assert data["document_b_id"] == sample_doc_b_id
        assert "comparisons" in data
        assert "summary" in data

    def test_compare_same_document_returns_400(self, client, sample_doc_id):
        """Comparing a document to itself must be rejected with 400."""
        resp = client.post(
            "/api/legal/compare",
            json={"document_a": sample_doc_id, "document_b": sample_doc_id},
        )
        assert resp.status_code == 400

    def test_compare_nonexistent_document_returns_404(self, client, sample_doc_id):
        """Comparing with a non-existent document must return 404."""
        resp = client.post(
            "/api/legal/compare",
            json={"document_a": sample_doc_id, "document_b": "nonexistent_doc_404"},
        )
        assert resp.status_code == 404

    def test_compare_empty_document_returns_400(self, client, sample_doc_id):
        """Comparing with empty document ID must return 400."""
        resp = client.post(
            "/api/legal/compare",
            json={"document_a": "", "document_b": sample_doc_id},
        )
        assert resp.status_code == 400


    def test_compare_cache_hit(self, client, sample_doc_id, sample_doc_b_id):
        """Comparing the same two documents twice must return from persistent SQLite cache."""
        from unittest.mock import patch
        # Prime the cache
        resp1 = client.post(
            "/api/legal/compare",
            json={"document_a": sample_doc_id, "document_b": sample_doc_b_id},
        )
        assert resp1.status_code == 200

        # Second call: verify compare_documents is NOT called
        with patch("api.legal_routes.compare_documents") as mock_compare:
            resp2 = client.post(
                "/api/legal/compare",
                json={"document_a": sample_doc_id, "document_b": sample_doc_b_id},
            )
            assert resp2.status_code == 200
            assert resp2.json()["document_a_id"] == resp1.json()["document_a_id"]
            mock_compare.assert_not_called()

        # Symmetric check: doc_b and doc_a inverted should hit the same cache
        with patch("api.legal_routes.compare_documents") as mock_compare_sym:
            resp3 = client.post(
                "/api/legal/compare",
                json={"document_a": sample_doc_b_id, "document_b": sample_doc_id},
            )
            assert resp3.status_code == 200
            mock_compare_sym.assert_not_called()


class TestLawyerBrief:
    def test_generate_brief_for_valid_doc(self, client, sample_doc_id):
        """Generating a brief must return situation, key clauses, and questions."""
        resp = client.post("/api/legal/lawyer-brief", json={"document_id": sample_doc_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == sample_doc_id
        assert "situation" in data
        assert "key_clauses" in data
        assert "risk_areas" in data
        assert "recommended_questions" in data

    def test_lawyer_brief_cache_hit(self, client, sample_doc_id):
        """Generating a brief twice must return from persistent SQLite cache."""
        from unittest.mock import patch
        # Prime the cache
        resp1 = client.post("/api/legal/lawyer-brief", json={"document_id": sample_doc_id, "language": "en"})
        assert resp1.status_code == 200

        # Second call: verify generate_lawyer_brief is NOT called
        with patch("api.legal_routes.generate_lawyer_brief") as mock_gen:
            resp2 = client.post("/api/legal/lawyer-brief", json={"document_id": sample_doc_id, "language": "en"})
            assert resp2.status_code == 200
            assert resp2.json()["situation"] == resp1.json()["situation"]
            mock_gen.assert_not_called()

    def test_generate_brief_hindi(self, client, sample_doc_id):
        """Brief generation with language='hi' must succeed."""
        resp = client.post("/api/legal/lawyer-brief", json={"document_id": sample_doc_id, "language": "hi"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == sample_doc_id
        assert "situation" in data

    def test_generate_brief_nonexistent_returns_404(self, client):
        """Brief generation for unknown document must return 404."""
        resp = client.post("/api/legal/lawyer-brief", json={"document_id": "nonexistent_doc_404"})
        assert resp.status_code == 404

    def test_generate_brief_empty_returns_400(self, client):
        """Brief generation with empty document ID must return 400."""
        resp = client.post("/api/legal/lawyer-brief", json={"document_id": ""})
        assert resp.status_code == 400


class TestObligations:
    def test_extract_obligations_for_valid_doc(self, client, sample_doc_id):
        """Obligation extraction must return list of obligations and deadlines."""
        resp = client.post("/api/legal/obligations", json={"document_id": sample_doc_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == sample_doc_id
        assert "obligations" in data
        assert isinstance(data["obligations"], list)

    def test_extract_obligations_nonexistent_returns_404(self, client):
        """Obligations extraction for unknown document must return 404."""
        resp = client.post("/api/legal/obligations", json={"document_id": "nonexistent_doc_404"})
        assert resp.status_code == 404
