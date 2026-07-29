"""
Voice Profile Management API — create, list, delete saved voices.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from backend.services.voice_manager import voice_manager

router = APIRouter(prefix="/api/voices", tags=["Voice Profiles"])


@router.get("/")
async def list_voices():
    """List all saved voice profiles."""
    return voice_manager.list_voices()


@router.get("/{voice_id}")
async def get_voice(voice_id: str):
    """Get a specific voice profile."""
    voice = voice_manager.get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.post("/upload")
async def create_voice_from_upload(
    name: str = Form(...),
    audio: UploadFile = File(...),
    reference_text: str = Form(""),
):
    """
    Create a voice profile by uploading a single reference audio (10-30s).
    """
    try:
        content = await audio.read()
        suffix = Path(audio.filename or "audio.wav").suffix or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        profile = voice_manager.create_voice_from_audio(
            name=name,
            audio_path=tmp_path,
            reference_text=reference_text or None,
        )

        Path(tmp_path).unlink(missing_ok=True)
        return profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-recordings")
async def create_voice_from_recordings(
    name: str = Form(...),
    voice_id: str = Form(...),
):
    """
    Build a voice profile from recorded sentences.
    Called after user finishes recording multiple sentences.
    """
    try:
        profile = voice_manager.create_voice_from_recordings(
            name=name,
            voice_id=voice_id,
        )
        return profile
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{voice_id}")
async def update_voice(voice_id: str, name: str = Form(...)):
    """Update voice profile name."""
    result = voice_manager.update_voice(voice_id, name=name)
    if not result:
        raise HTTPException(status_code=404, detail="Voice not found")
    return result


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a voice profile and its data."""
    if voice_manager.delete_voice(voice_id):
        return {"status": "deleted", "voice_id": voice_id}
    raise HTTPException(status_code=404, detail="Voice not found")
