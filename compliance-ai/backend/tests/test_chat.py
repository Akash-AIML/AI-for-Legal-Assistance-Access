"""Tests for chat and LangGraph decision workflow endpoints."""
from __future__ import annotations


class TestChatSessions:
    def test_list_sessions(self, client, auth_headers):
        """User can list their active chat sessions."""
        resp = client.get("/api/chat/sessions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_get_history_empty_session(self, client, auth_headers):
        """History for a new session returns empty message list."""
        resp = client.get("/api/chat/history?session_id=test_empty_session_123", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)


class TestChatInteraction:
    def test_chat_empty_question_returns_error(self, client, auth_headers):
        """Empty question returns error indicator."""
        resp = client.post(
            "/api/chat",
            json={"question": "   "},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_chat_valid_question_invokes_engine(self, client, auth_headers):
        """Asking a valid question runs the LangGraph engine and returns an answer or clarification."""
        resp = client.post(
            "/api/chat",
            json={"question": "What is the policy on annual leave and notice periods?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data or "clarification" in data or "decision" in data

    def test_multi_turn_chat_session_accumulates_context(self, client, auth_headers):
        """Multi-turn chat session carries context and history across consecutive messages."""
        # Turn 1: Initial query
        resp1 = client.post(
            "/api/chat",
            json={"question": "What is the policy regarding residential rental agreements in Delhi?"},
            headers=auth_headers,
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        session_id = data1.get("session_id")
        assert session_id is not None

        # Turn 2: Follow-up query in same session
        resp2 = client.post(
            "/api/chat",
            json={
                "question": "What is the standard notice period for that?",
                "session_id": session_id,
            },
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2.get("session_id") == session_id

        # Verify history persistence
        history_resp = client.get(f"/api/chat/history?session_id={session_id}", headers=auth_headers)
        assert history_resp.status_code == 200
        messages = history_resp.json().get("messages", [])
        assert len(messages) >= 4  # 2 user messages + 2 assistant responses



class TestChatStream:
    def test_chat_stream_empty_question_returns_400(self, client, auth_headers):
        """Empty question on /stream returns 400 Bad Request."""
        resp = client.post(
            "/api/chat/stream",
            json={"question": "   "},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_chat_stream_returns_sse_events(self, client, auth_headers):
        """Verify stream returns text/event-stream content type."""
        resp = client.post("/api/chat/stream", json={"question": "What is the notice period?"}, headers=auth_headers)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_chat_stream_sse_endpoint(self, client, auth_headers):
        """Stream endpoint returns text/event-stream with meta and done markers."""
        resp = client.post(
            "/api/chat/stream",
            json={"question": "What is the policy on annual leave?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body_text = resp.text
        assert "data: " in body_text
        assert "[DONE]" in body_text


