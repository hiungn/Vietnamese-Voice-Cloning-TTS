"""
Recording API — record multiple sentences to build a voice profile.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from backend.services.recording_manager import recording_manager

router = APIRouter(prefix="/api/recordings", tags=["Recordings"])


@router.get("/scripts")
async def get_scripts():
    """Get list of sentences to record."""
    scripts = recording_manager.get_scripts()
    return {"scripts": scripts, "total": len(scripts)}


@router.post("/new-session")
async def create_recording_session():
    """
    Start a new recording session.
    Returns a voice_id to associate recordings with.
    """
    voice_id = uuid.uuid4().hex[:12]
    return {"voice_id": voice_id}


@router.post("/save")
async def save_recording(
    voice_id: str = Form(...),
    index: int = Form(...),
    audio: UploadFile = File(...),
):
    """Save a single recording for a voice profile."""
    try:
        content = await audio.read()
        result = recording_manager.save_recording(
            voice_id=voice_id,
            index=index,
            audio_bytes=content,
            filename=audio.filename or "recording.webm",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{voice_id}")
async def get_recording_progress(voice_id: str):
    """Get which sentences have been recorded."""
    indices = recording_manager.get_recorded_indices(voice_id)
    total = len(recording_manager.get_scripts())
    return {
        "voice_id": voice_id,
        "recorded": indices,
        "count": len(indices),
        "total": total,
    }


@router.delete("/{voice_id}/{index}")
async def delete_recording(voice_id: str, index: int):
    """Delete a specific recording."""
    if recording_manager.delete_recording(voice_id, index):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Recording not found")
