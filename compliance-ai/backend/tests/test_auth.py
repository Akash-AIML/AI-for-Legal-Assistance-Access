"""Tests for authentication endpoints."""
from __future__ import annotations


class TestLogin:
    def test_login_success_returns_token(self, client):
        """Valid credentials must return a JWT access token."""
        resp = client.post("/api/auth/login", json={"username": "asha", "password": "demo123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 10
        assert data["user"]["username"] == "asha"

    def test_login_wrong_password_returns_401(self, client):
        """Wrong password must be rejected with 401."""
        resp = client.post("/api/auth/login", json={"username": "asha", "password": "wrongpassword"})
        assert resp.status_code == 401

    def test_login_unknown_user_returns_401(self, client):
        """Non-existent username must be rejected with 401."""
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "demo123"})
        assert resp.status_code == 401

    def test_login_empty_body_returns_422(self, client):
        """Empty body must fail Pydantic validation with 422."""
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 422

    def test_password_not_in_response(self, client):
        """Password hash must never be returned in the login response."""
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "demo123"})
        assert "password" not in resp.text


class TestMe:
    def test_me_with_valid_token(self, client, auth_headers):
        """Authenticated /me must return user profile."""
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "Admin"

    def test_me_without_token_returns_401(self, client):
        """Unauthenticated request to /me must return 401."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        """Invalid bearer token must return 401."""
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


class TestUsers:
    def test_admin_can_list_users(self, client, auth_headers):
        """Admin should be able to list all users."""
        resp = client.get("/api/auth/users", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_employee_cannot_list_users(self, client, employee_headers):
        """Employee should not be able to list users — 403 expected."""
        resp = client.get("/api/auth/users", headers=employee_headers)
        assert resp.status_code == 403


class TestRegister:
    def test_register_new_user_success(self, client):
        """Registering a new citizen user should succeed and return access token."""
        import uuid
        unique_username = f"citizen_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": unique_username,
            "password": "strongpassword123",
            "name": "Ravi Kumar",
            "role": "Citizen",
            "department": "Tenant Legal Aid",
            "jurisdiction": "IN",
        }
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == unique_username
        assert data["user"]["name"] == "Ravi Kumar"

    def test_register_existing_username_returns_400(self, client):
        """Registering with an already existing username must return 400."""
        payload = {
            "username": "asha",
            "password": "anotherpassword123",
            "name": "Duplicate User",
        }
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json().get("detail", "")

    def test_register_short_password_returns_400(self, client):
        """Password shorter than 6 characters must be rejected with 400."""
        payload = {
            "username": "short_pw_user",
            "password": "123",
            "name": "Short PW",
        }
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400
        assert "at least 6 characters" in resp.json().get("detail", "")
