"""Tests for document management endpoints."""
from __future__ import annotations

import io


class TestListDocuments:
    def test_list_documents_returns_200(self, client):
        """Unauthenticated list must return 200 with documents list."""
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
        assert "chunk_count" in data
        assert isinstance(data["chunk_count"], int)


class TestUpload:
    def test_upload_text_file(self, client):
        """Uploading a plain text file should return chunks_indexed >= 0."""
        content = b"This is a test compliance policy document. Section 1: All employees must follow the code of conduct."
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("test_policy.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "filename" in data
        assert "chunks_indexed" in data
        assert isinstance(data["chunks_indexed"], int)

    def test_upload_markdown_file(self, client):
        """Uploading a Markdown file should return chunks_indexed >= 0."""
        content = b"# Test Policy\n\n## Section 1\nAll employees must comply with this policy.\n\n## Section 2\nViolations will result in disciplinary action."
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("policy.md", io.BytesIO(content), "text/markdown")},
        )
        assert resp.status_code == 200

    def test_upload_too_large_file_returns_413(self, client):
        """Files exceeding 10MB must be rejected with 413."""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("large.txt", io.BytesIO(large_content), "text/plain")},
        )
        assert resp.status_code == 413

    def test_upload_disallowed_extension_returns_400(self, client):
        """Files with disallowed extensions like .exe must be rejected with 400."""
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("malicious.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json().get("detail", "")

    def test_upload_script_extension_returns_400(self, client):
        """Files with script extensions like .py must be rejected with 400."""
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")},
        )
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json().get("detail", "")

    def test_upload_fake_pdf_fails_magic_bytes(self, client):
        """A file with .pdf extension but lacking %PDF header must be rejected with 400."""
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("fake.pdf", io.BytesIO(b"NOT A REAL PDF FILE"), "application/pdf")},
        )
        assert resp.status_code == 400
        assert "not a valid PDF" in resp.json().get("detail", "")

    def test_upload_fake_docx_fails_magic_bytes(self, client):
        """A file with .docx extension but lacking PK zip header must be rejected with 400."""
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("fake.docx", io.BytesIO(b"NOT A REAL DOCX FILE"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 400
        assert "not a valid DOCX" in resp.json().get("detail", "")

    def test_upload_disguised_executable_in_txt_fails(self, client):
        """A binary executable disguised as .txt must be rejected with 400."""
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("disguised.txt", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "text/plain")},
        )
        assert resp.status_code == 400
        assert "binary or executable content detected" in resp.json().get("detail", "")


class TestRBAC:
    def test_reindex_requires_admin(self, client, employee_headers):
        """Reindex must be restricted to Admin/HR/Compliance — Employee gets 403."""
        resp = client.post("/api/documents/reindex", headers=employee_headers)
        assert resp.status_code == 403

    def test_reindex_allowed_for_admin(self, client, auth_headers):
        """Reindex must succeed for Admin."""
        resp = client.post("/api/documents/reindex", headers=auth_headers)
        assert resp.status_code == 200
