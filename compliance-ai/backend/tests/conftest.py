import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Force offline mode for testing to ensure instant, deterministic test runs
os.environ["LLM_OFFLINE"] = "true"

# Add src to sys.path so imports work without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    """Return a TestClient wrapping the FastAPI app."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    """Return Authorization headers for the admin demo user."""
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "demo123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def employee_headers(client):
    """Return Authorization headers for a low-privilege Employee user."""
    resp = client.post("/api/auth/login", json={"username": "asha", "password": "demo123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
