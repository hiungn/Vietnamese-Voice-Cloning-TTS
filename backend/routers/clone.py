"""
Voice Cloning API — quick clone with 10-30s reference audio.
"""

import io
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.tts_engine import tts_engine

router = APIRouter(prefix="/api/clone", tags=["Voice Cloning"])


@router.post("/quick")
async def quick_clone(
    text: str = Form(...),
    reference_audio: UploadFile = File(...),
    reference_text: str = Form(""),
    speed: float = Form(1.0),
    format: str = Form("wav"),
):
    """
    Quick voice cloning: upload 10-30s reference audio + text → get cloned speech.
    """
    try:
        # Save uploaded audio to temp file
        content = await reference_audio.read()
        suffix = Path(reference_audio.filename or "audio.wav").suffix or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        filepath, audio_bytes = tts_engine.clone_voice(
            text=text,
            reference_audio_path=tmp_path,
            reference_text=reference_text or None,
            speed=speed,
            output_format=format,
        )

        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

        media_type = "audio/mpeg" if format == "mp3" else "audio/wav"
        filename = Path(filepath).name

        return StreamingResponse(
            content=io.BytesIO(audio_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/with-voice")
async def clone_with_saved_voice(
    text: str = Form(...),
    voice_id: str = Form(...),
    speed: float = Form(1.0),
    format: str = Form("wav"),
):
    """
    Clone using a saved voice profile.
    """
    try:
        filepath, audio_bytes = tts_engine.synthesize_with_voice_profile(
            text=text,
            voice_id=voice_id,
            speed=speed,
            output_format=format,
        )

        media_type = "audio/mpeg" if format == "mp3" else "audio/wav"
        filename = Path(filepath).name

        return StreamingResponse(
            content=io.BytesIO(audio_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
