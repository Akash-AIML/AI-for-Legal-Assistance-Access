"""Tests for Role-Based Access Control across all sensitive endpoints."""
from __future__ import annotations


class TestAuditAccess:
    def test_employee_cannot_access_audit_log(self, client, employee_headers):
        """Employees must not be able to access /api/audit/recent — 403 expected."""
        resp = client.get("/api/audit/recent", headers=employee_headers)
        assert resp.status_code == 403

    def test_admin_can_access_audit_log(self, client, auth_headers):
        """Admin must be able to access /api/audit/recent."""
        resp = client.get("/api/audit/recent", headers=auth_headers)
        assert resp.status_code == 200

    def test_unauthenticated_cannot_access_audit_log(self, client):
        """Unauthenticated requests to /api/audit/recent must return 401."""
        resp = client.get("/api/audit/recent")
        assert resp.status_code == 401


class TestEscalationAccess:
    def test_employee_can_view_own_escalations(self, client, employee_headers):
        """Employees must be able to list their own escalations."""
        resp = client.get("/api/escalations", headers=employee_headers)
        assert resp.status_code == 200

    def test_employee_cannot_resolve_escalations(self, client, employee_headers):
        """Employees must not be able to resolve escalations — 403 expected."""
        resp = client.post(
            "/api/escalations/resolve",
            json={"escalation_id": "ESC-00001", "resolution": "resolved"},
            headers=employee_headers,
        )
        assert resp.status_code == 403

    def test_admin_can_list_all_escalations(self, client, auth_headers):
        """Admin must be able to list all escalations."""
        resp = client.get("/api/escalations", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "escalations" in data


class TestDocumentStatusRBAC:
    def test_employee_cannot_update_document_status(self, client, employee_headers):
        """Employees must not be able to update document status — 403 expected."""
        resp = client.post(
            "/api/documents/status",
            json={"document_id": "doc-001", "status": "ACTIVE"},
            headers=employee_headers,
        )
        assert resp.status_code == 403

    def test_employee_cannot_delete_document(self, client, employee_headers):
        """Employees must not be able to delete documents — 403 expected."""
        resp = client.delete("/api/documents/doc-001", headers=employee_headers)
        assert resp.status_code == 403
