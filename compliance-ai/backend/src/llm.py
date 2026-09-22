"""Thin OpenAI-compatible client for chat, embeddings, and (optional) audio.

All providers implementing the OpenAI API contract work: OpenAI, and any
self-hosted / compatible gateway that accepts a base_url + api_key.

If no API key is configured, a deterministic hash-based embedding fallback and
a stub chat responder are used so the pipeline runs fully offline (demo mode).
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from typing import Any, Iterable, Sequence

from openai import OpenAI

from config import get_settings

_settings = get_settings()
logger = logging.getLogger(__name__)

OFFLINE_MODE = _settings.llm_offline


import threading

_client_instance: OpenAI | None = None
_client_lock = threading.Lock()


def _client() -> OpenAI:
    """Thread-safe singleton OpenAI client preserving HTTP connection pooling and Keep-Alive."""
    global _client_instance
    with _client_lock:
        if _client_instance is None:
            api_key = (
                _settings.groq_api_key
                or _settings.openai_api_key
                or os.environ.get("GROQ_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
                or "sk-local"
            )
            _client_instance = OpenAI(api_key=api_key, base_url=_settings.openai_base_url)
        return _client_instance


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.1,
    model: str | None = None,
    max_tokens: int | None = None,
    response_format: dict[str, Any] | None = None,
) -> str:
    """Return a plain-text completion for the given OpenAI-style messages."""
    if OFFLINE_MODE:
        return _offline_chat(messages)
    selected_model = model or _settings.openai_chat_model
    t0 = time.time()
    logger.debug("LLM Chat starting | model=%s | max_tokens=%s | messages=%d", selected_model, max_tokens, len(messages))
    kwargs: dict[str, Any] = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format
    try:
        resp = _client().chat.completions.create(**kwargs)
        txt = resp.choices[0].message.content or ""
        dt = (time.time() - t0) * 1000.0
        logger.debug("LLM Chat finished in %.1fms | output_len=%d chars", dt, len(txt))
        return txt
    except Exception as exc:
        logger.warning("LLM Chat API call failed (%s). Falling back to resilient offline responder.", exc)
        return _offline_chat(messages)


def stream_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.1,
    model: str | None = None,
) -> Iterable[str]:
    """Stream chat completion tokens from the configured LLM."""
    if OFFLINE_MODE:
        for tok in _offline_chat(messages).split(" "):
            yield tok + " "
        return
    selected_model = model or _settings.openai_chat_model
    t0 = time.time()
    logger.debug("LLM Stream Chat starting | model=%s", selected_model)
    try:
        resp = _client().chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        first_token = True
        for chunk in resp:
            if first_token:
                ttft = (time.time() - t0) * 1000.0
                logger.debug("Stream TTFT: %.1fms", ttft)
                first_token = False
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except Exception as exc:
        logger.warning("LLM Stream API call failed (%s). Falling back to resilient offline tokens.", exc)
        for tok in _offline_chat(messages).split(" "):
            yield tok + " "



def embed_texts(texts: Sequence[str], input_type: str = "query") -> list[list[float]]:
    """Batch-embed texts using the configured embedding model."""
    if OFFLINE_MODE or "groq.com" in _settings.openai_base_url.lower():
        # Groq is an ultra-fast LLM inference gateway without an embedding API; use deterministic embeddings
        return [_offline_embed(t) for t in texts]

    t0 = time.time()
    logger.debug("Embedding starting | model=%s | batch_size=%d | type=%s", _settings.openai_embed_model, len(texts), input_type)

    extra: dict[str, Any] = {}
    if "nvidia" in _settings.openai_base_url.lower() or "nvidia" in _settings.openai_embed_model.lower():
        extra["extra_body"] = {"input_type": input_type}

    try:
        resp = _client().embeddings.create(
            model=_settings.openai_embed_model,
            input=list(texts),
            **extra
        )
        ordered = sorted(resp.data, key=lambda d: d.index)
        dt = (time.time() - t0) * 1000.0
        logger.debug("Embedding finished in %.1fms | dim=%d", dt, len(ordered[0].embedding) if ordered else 0)
        return [d.embedding for d in ordered]
    except Exception as exc:
        logger.warning("Embedding API call failed (%s). Falling back to resilient offline embeddings.", exc)
        return [_offline_embed(t) for t in texts]


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm", mime: str = "audio/webm") -> str:
    """Transcribe speech using the configured OpenAI-compatible provider's Whisper.

    Unlike chat/embeddings there is no deterministic offline fallback, so this
    requires a real provider + API key (the .env OPENAI_BASE_URL / OPENAI_API_KEY).
    """
    key = (
        _settings.groq_api_key
        or _settings.openai_api_key
        or os.environ.get("GROQ_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    if not key:
        raise RuntimeError("Speech-to-text needs an API key. Add it to backend/.env.")
    resp = _client().audio.transcriptions.create(
        model=_settings.openai_audio_model,
        file=(filename or "audio.webm", audio_bytes, mime),
    )
    return (getattr(resp, "text", None) or "").strip()


def synthesize_speech(text: str, voice: str = "alloy") -> bytes:
    """Synthesize text into speech audio bytes using OpenAI-compatible audio API."""
    if not _settings.openai_api_key:
        raise RuntimeError("Speech synthesis requires OPENAI_API_KEY in .env.")

    # Primary model: tts-1, with fallback to gpt-4o-mini-tts or audio model
    models_to_try = ["tts-1", "gpt-4o-mini-tts", "gpt-4o-audio-preview"]
    last_err = None
    for model_name in models_to_try:
        try:
            resp = _client().audio.speech.create(
                model=model_name,
                voice=voice,
                input=text[:4096],
            )
            if hasattr(resp, "content"):
                return resp.content
            if hasattr(resp, "read"):
                return resp.read()
            return bytes(resp)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"TTS audio synthesis failed across models: {last_err}")


tts_text = synthesize_speech


# ---------------------------------------------------------------------------
# Offline fallbacks (demo mode, no API key)
# ---------------------------------------------------------------------------

_DIM = 2048

# Semantic concept clusters mapping legal terminology to coordinate subspaces
_LEGAL_SEMANTIC_CLUSTERS: list[tuple[set[str], tuple[str, ...], int]] = [
    ({"termination", "terminate", "terminated", "terminating", "cancel", "cancellation", "rescind", "breach", "default", "severance", "exit", "notice"}, ("termin", "cancel", "rescind", "breach"), 0),
    ({"payment", "pay", "paid", "paying", "fee", "fees", "compensation", "invoice", "price", "rate", "cost", "penalty", "liquidated", "interest", "billing", "amount"}, ("pay", "invoic", "fee", "cost", "bill"), 128),
    ({"liability", "liable", "indemnity", "indemnify", "indemnification", "loss", "losses", "harmless", "cap", "limitation", "warranty", "warranties", "damages"}, ("liab", "indemn", "damag", "warrant"), 256),
    ({"confidential", "confidentiality", "proprietary", "trade", "secret", "secrets", "patent", "copyright", "intellectual", "property", "ownership", "assignment", "license"}, ("confid", "propriet", "patent", "intellect"), 384),
    ({"governing", "law", "jurisdiction", "court", "arbitration", "dispute", "resolution", "venue", "tribunal", "compliance", "regulatory", "gdpr", "statute", "obligation"}, ("govern", "jurisdict", "arbitrat", "disput"), 512),
    ({"contractor", "client", "employee", "employer", "tenant", "landlord", "party", "parties", "vendor", "supplier", "worker", "freelancer", "consultant"}, ("contract", "employ", "tenant", "landlord", "vendor"), 640),
]


def _offline_embed(text: str) -> list[float]:
    """Semantic concept-anchored embedding with subword n-grams (preserves cosine similarity offline)."""
    vec = [0.0] * _DIM
    toks = re.findall(r"[a-z0-9]+", text.lower())
    for tok in toks:
        # 1. Project legal concept clusters into semantic subspaces
        for cluster, roots, offset in _LEGAL_SEMANTIC_CLUSTERS:
            if tok in cluster or any(tok.startswith(root) for root in roots):
                for i in range(64):
                    vec[offset + i] += 4.0
        # 2. Subword character n-grams (3-grams, 4-grams) for morphological proximity
        padded = f"^{tok}$"
        for n in (3, 4):
            for i in range(len(padded) - n + 1):
                ngram = padded[i : i + n]
                h = int(hashlib.sha256(ngram.encode()).hexdigest()[:8], 16)
                vec[1024 + (h % 1024)] += 0.5
    norm = (sum(v * v for v in vec) ** 0.5) or 1.0
    return [v / norm for v in vec]


def _offline_chat(messages: list[dict[str, str]]) -> str:
    """Return a deterministic offline stub response."""
    last = messages[-1].get("content", "") if messages else ""
    return (
        "[offline demo mode: no LLM configured. Configure OPENAI_BASE_URL and "
        f"OPENAI_API_KEY in .env for real answers.]\n\nQuestion: {last[:200]}"
    )