'''Text-to-speech endpoint for generating audio from assistant answers.'''
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

from auth import get_current_user
from llm import tts_text

router = APIRouter(prefix="/api/tts", tags=["tts"])

@router.post("")
def tts(payload: dict, user: dict = Depends(get_current_user)):
    """Generate MP3 audio for the supplied ``text``.

    The request body must be JSON ``{"text": "..."}``. The endpoint returns a
    ``StreamingResponse`` with ``audio/mpeg`` content. Errors are returned as
    ``HTTPException`` with a clear message.
    """
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(400, "Empty text")
    try:
        audio_bytes = tts_text(text)
    except Exception as e:
        raise HTTPException(500, f"TTS generation failed: {e}")
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
