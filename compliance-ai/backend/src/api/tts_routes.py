"""Text-to-speech endpoint for generating audio from assistant answers."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth import get_current_user
from llm import tts_text

router = APIRouter(prefix="/api/tts", tags=["Speech & Voice"])


class TTSRequest(BaseModel):
    text: str


@router.post("", operation_id="tts_stream_audio", description="Generate MP3 streaming audio for the supplied text.")
def tts(body: TTSRequest, user: dict = Depends(get_current_user)) -> StreamingResponse:
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Empty text")
    try:
        audio_bytes = tts_text(text)
    except Exception as e:
        raise HTTPException(500, f"TTS generation failed: {e}")
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")

