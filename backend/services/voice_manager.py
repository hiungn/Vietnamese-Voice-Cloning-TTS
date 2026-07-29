"""
Manages voice profiles — saved reference audios and trained voices.
"""

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from backend.config import VOICES_DIR, VOICES_META, RECORDINGS_DIR


def _load_voices() -> dict:
    if VOICES_META.exists():
        return json.loads(VOICES_META.read_text(encoding="utf-8"))
    return {}


def _save_voices(data: dict):
    VOICES_META.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class VoiceManager:
    """CRUD for voice profiles."""

    def list_voices(self) -> list[dict]:
        voices = _load_voices()
        result = []
        for vid, v in voices.items():
            result.append({"id": vid, **v})
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_voice(self, voice_id: str) -> Optional[dict]:
        voices = _load_voices()
        v = voices.get(voice_id)
        if v:
            return {"id": voice_id, **v}
        return None

    def create_voice_from_audio(
        self,
        name: str,
        audio_path: str,
        reference_text: Optional[str] = None,
    ) -> dict:
        """
        Create a voice profile from a single reference audio file.
        The audio is copied into the voices directory.
        """
        voice_id = uuid.uuid4().hex[:12]
        voice_dir = VOICES_DIR / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Copy and convert reference audio to WAV
        src = Path(audio_path)
        dest = voice_dir / "reference.wav"

        audio = AudioSegment.from_file(str(src))
        # Ensure reasonable length (10-30s recommended)
        duration_sec = len(audio) / 1000.0
        audio.export(str(dest), format="wav")

        profile = {
            "name": name,
            "type": "reference",
            "reference_audio": str(dest),
            "reference_text": reference_text or "",
            "duration_sec": round(duration_sec, 1),
            "created_at": datetime.now().isoformat(),
            "recordings_count": 0,
        }

        voices = _load_voices()
        voices[voice_id] = profile
        _save_voices(voices)

        return {"id": voice_id, **profile}

    def create_voice_from_recordings(
        self,
        name: str,
        voice_id: Optional[str] = None,
    ) -> dict:
        """
        Create/update a voice profile from multiple recorded sentences.
        Combines best recordings into reference audio for cloning.
        """
        if voice_id is None:
            voice_id = uuid.uuid4().hex[:12]

        voice_dir = VOICES_DIR / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        rec_dir = RECORDINGS_DIR / voice_id
        if not rec_dir.exists() or not any(rec_dir.iterdir()):
            raise FileNotFoundError(f"No recordings found for voice '{voice_id}'")

        # Collect all WAV recordings
        wav_files = sorted(rec_dir.glob("*.wav"))
        if not wav_files:
            raise FileNotFoundError("No WAV recordings found")

        # Use the first recording as reference (best quality single sample)
        # and concatenate a few for a longer reference
        combined = AudioSegment.empty()
        for wf in wav_files[:5]:  # Use up to 5 recordings as reference
            seg = AudioSegment.from_wav(str(wf))
            combined += seg + AudioSegment.silent(duration=300)

        # Trim to max 30s
        if len(combined) > 30000:
            combined = combined[:30000]

        dest = voice_dir / "reference.wav"
        combined.export(str(dest), format="wav")

        duration_sec = len(combined) / 1000.0

        profile = {
            "name": name,
            "type": "recorded",
            "reference_audio": str(dest),
            "reference_text": "",
            "duration_sec": round(duration_sec, 1),
            "created_at": datetime.now().isoformat(),
            "recordings_count": len(wav_files),
        }

        voices = _load_voices()
        voices[voice_id] = profile
        _save_voices(voices)

        return {"id": voice_id, **profile}

    def delete_voice(self, voice_id: str) -> bool:
        voices = _load_voices()
        if voice_id not in voices:
            return False

        # Remove voice directory
        voice_dir = VOICES_DIR / voice_id
        if voice_dir.exists():
            shutil.rmtree(voice_dir)

        # Remove recordings
        rec_dir = RECORDINGS_DIR / voice_id
        if rec_dir.exists():
            shutil.rmtree(rec_dir)

        del voices[voice_id]
        _save_voices(voices)
        return True

    def update_voice(self, voice_id: str, name: Optional[str] = None) -> Optional[dict]:
        voices = _load_voices()
        if voice_id not in voices:
            return None
        if name:
            voices[voice_id]["name"] = name
        _save_voices(voices)
        return {"id": voice_id, **voices[voice_id]}


voice_manager = VoiceManager()
