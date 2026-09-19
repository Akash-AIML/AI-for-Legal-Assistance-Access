"""Thin OpenAI-compatible client for chat, embeddings, and (optional) audio.

All providers implementing the OpenAI API contract work: OpenAI, and any
self-hosted / compatible gateway that accepts a base_url + api_key.

If no API key is configured, a deterministic hash-based embedding fallback and
a stub chat responder are used so the pipeline runs fully offline (demo mode).
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Iterable, Sequence

from openai import OpenAI

from config import get_settings

_settings = get_settings()

OFFLINE_MODE = _settings.llm_offline


def _client() -> OpenAI:
    return OpenAI(api_key=_settings.openai_api_key or "sk-local", base_url=_settings.openai_base_url)


import time

def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.1,
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Return a plain-text completion for the given OpenAI-style messages."""
    if OFFLINE_MODE:
        return _offline_chat(messages)
    selected_model = model or _settings.openai_chat_model
    t0 = time.time()
    print(f"\033[93m⏱️ [PERF] LLM Chat starting | Model: {selected_model} | MaxTokens: {max_tokens} | Messages: {len(messages)}\033[0m", flush=True)
    resp = _client().chat.completions.create(
        model=selected_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    txt = resp.choices[0].message.content or ""
    dt = (time.time() - t0) * 1000.0
    print(f"\033[92m⏱️ [PERF] LLM Chat finished in {dt:.1f}ms | Output len: {len(txt)} chars\033[0m", flush=True)
    return txt


def stream_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.1,
    model: str | None = None,
) -> Iterable[str]:
    if OFFLINE_MODE:
        for tok in _offline_chat(messages).split(" "):
            yield tok + " "
        return
    selected_model = model or _settings.openai_chat_model
    t0 = time.time()
    print(f"\033[93m⏱️ [PERF] LLM Stream Chat starting | Model: {selected_model}\033[0m", flush=True)
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
            print(f"\033[92m⏱️ [PERF] Stream Time-To-First-Token (TTFT): {ttft:.1f}ms\033[0m", flush=True)
            first_token = False
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


def embed_texts(texts: Sequence[str], input_type: str = "query") -> list[list[float]]:
    """Batch-embed texts using the configured embedding model."""
    if OFFLINE_MODE:
        return [_offline_embed(t) for t in texts]
    
    t0 = time.time()
    print(f"\033[93m⏱️ [PERF] Embedding starting | Model: {_settings.openai_embed_model} | Batch size: {len(texts)} | Type: {input_type}\033[0m", flush=True)

    extra: dict[str, Any] = {}
    if "nvidia" in _settings.openai_base_url.lower() or "nvidia" in _settings.openai_embed_model.lower():
        extra["extra_body"] = {"input_type": input_type}

    resp = _client().embeddings.create(
        model=_settings.openai_embed_model,
        input=list(texts),
        **extra
    )
    # sort by index to keep order stable
    ordered = sorted(resp.data, key=lambda d: d.index)
    dt = (time.time() - t0) * 1000.0
    print(f"\033[92m⏱️ [PERF] Embedding finished in {dt:.1f}ms (dim={len(ordered[0].embedding) if ordered else 0})\033[0m", flush=True)
    return [d.embedding for d in ordered]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm", mime: str = "audio/webm") -> str:
    """Transcribe speech using the configured OpenAI-compatible provider's Whisper.

    Unlike chat/embeddings there is no deterministic offline fallback, so this
    requires a real provider + API key (the .env OPENAI_BASE_URL / OPENAI_API_KEY).
    """
    if not _settings.openai_api_key:
        raise RuntimeError("Speech-to-text needs OPENAI_API_KEY. Add it to backend/.env.")
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

_DIM = 64


def _offline_embed(text: str) -> list[float]:
    """Deterministic bag-of-word hashed embedding (demo-only, not semantic)."""
    vec = [0.0] * _DIM
    toks = re.findall(r"[a-z0-9]+", text.lower())
    for tok in toks:
        idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % _DIM
        vec[idx] += 1.0
    norm = (sum(v * v for v in vec) ** 0.5) or 1.0
    return [v / norm for v in vec]


def _offline_chat(messages: list[dict[str, str]]) -> str:
    last = messages[-1].get("content", "") if messages else ""
    return (
        "[offline demo mode: no LLM configured. Configure OPENAI_BASE_URL and "
        f"OPENAI_API_KEY in .env for real answers.]\n\nQuestion: {last[:200]}"
    )