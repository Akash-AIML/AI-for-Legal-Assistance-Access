"""Tests for LLM resilience against rate limits (429) and timeouts (504)."""
from unittest.mock import patch
from llm import chat, stream_chat


def test_llm_chat_rate_limit_429_resilience():
    """When LLM provider raises 429 Rate Limit, system gracefully falls back to offline response."""
    with patch("llm.OFFLINE_MODE", False):
        with patch("llm._client") as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Rate limit exceeded (429)")
            result = chat([{"role": "user", "content": "What are the terms?"}])
            assert isinstance(result, str)
            assert len(result) > 0


def test_llm_chat_timeout_504_resilience():
    """When LLM provider raises 504 Gateway Timeout, system gracefully falls back to offline response."""
    with patch("llm.OFFLINE_MODE", False):
        with patch("llm._client") as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Gateway Timeout (504)")
            result = chat([{"role": "user", "content": "What is the penalty?"}])
            assert isinstance(result, str)
            assert len(result) > 0


def test_llm_stream_chat_error_resilience():
    """When streaming LLM provider raises an error, system yields fallback tokens."""
    with patch("llm.OFFLINE_MODE", False):
        with patch("llm._client") as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("Connection error (502)")
            tokens = list(stream_chat([{"role": "user", "content": "Hello"}]))
            assert len(tokens) > 0
