"""Speech routes: transcribe uploaded audio via the configured Whisper provider."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from auth import get_current_user
from llm import synthesize_speech, transcribe_audio

router = APIRouter(prefix="/api/speech", tags=["speech"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty audio")
    try:
        mime = file.content_type or "audio/webm"
        text = transcribe_audio(data, file.filename or "audio.webm", mime)
        if not text:
            raise HTTPException(422, "no speech recognized")
        return {"text": text, "username": user["username"]}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001 - surface provider errors to the UI
        raise HTTPException(500, f"Transcription failed: {e}") from e


@router.post("/tts")
async def tts(payload: dict, user: dict = Depends(get_current_user)):
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(400, "empty text parameter")
    try:
        audio_bytes = synthesize_speech(text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Speech synthesis failed: {e}") from e