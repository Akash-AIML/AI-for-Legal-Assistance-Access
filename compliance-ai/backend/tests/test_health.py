"""Tests for the /api/health endpoint."""
from __future__ import annotations


def test_health_returns_200(client):
    """Health endpoint must return HTTP 200."""
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_schema(client):
    """Health response must contain required fields with correct types."""
    data = client.get("/api/health").json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "chunks" in data
    assert isinstance(data["chunks"], int)
    assert "documents" in data
    assert isinstance(data["documents"], int)
    assert "offline_mode" in data
    assert isinstance(data["offline_mode"], bool)


def test_openapi_json_accessible(client):
    """OpenAPI spec must be accessible at /api/openapi.json."""
    resp = client.get("/api/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "paths" in data
