"""
Voice Cloning TTS Engine using Fish Speech.

Fish Speech supports:
- Zero-shot voice cloning with 10-30s reference audio
- Fine-tuning with more data for higher quality
"""

import io
import uuid
import time
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Tuple

from backend.config import OUTPUT_DIR, SAMPLE_RATE


class TTSEngine:
    """Wrapper around Fish Speech for voice cloning inference."""

    def __init__(self):
        self._ready = False
        self._check_device()

    def _check_device(self):
        try:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            self._device = "cpu"
        print(f"TTS Engine: using {self._device}")

    def clone_voice(
        self,
        text: str,
        reference_audio_path: str,
        reference_text: Optional[str] = None,
        speed: float = 1.0,
        output_format: str = "wav",
    ) -> Tuple[str, bytes]:
        """
        Clone a voice using reference audio and synthesize new text.

        Returns:
            (output_filepath, audio_bytes)
        """
        uid = uuid.uuid4().hex[:8]
        wav_path = OUTPUT_DIR / f"clone_{uid}.wav"

        start = time.time()

        # Use Fish Speech CLI — most reliable method
        cmd = [
            "python", "-m", "tools.inference",
            "--text", text,
            "--reference_audio", str(reference_audio_path),
            "--output", str(wav_path),
            "--device", self._device,
        ]
        if reference_text:
            cmd.extend(["--reference_text", reference_text])

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # CPU can be slow
            )
            if proc.returncode != 0:
                # Try alternative CLI format
                cmd2 = [
                    "fish-speech", "infer",
                    "--text", text,
                    "--reference-audio", str(reference_audio_path),
                    "--output", str(wav_path),
                ]
                if reference_text:
                    cmd2.extend(["--reference-text", reference_text])

                proc2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=600)
                if proc2.returncode != 0:
                    raise RuntimeError(
                        f"Fish Speech inference failed:\n{proc.stderr}\n{proc2.stderr}"
                    )
        except FileNotFoundError:
            raise RuntimeError(
                "Fish Speech is not installed. Run: pip install fish-speech"
            )

        elapsed = time.time() - start
        print(f"Voice cloning completed in {elapsed:.1f}s -> {wav_path.name}")

        if not wav_path.exists():
            raise RuntimeError("Output audio file was not generated")

        audio_bytes = wav_path.read_bytes()

        # Convert to mp3 if requested
        if output_format == "mp3":
            audio_bytes = self._convert_to_mp3(audio_bytes)
            final_path = wav_path.with_suffix(".mp3")
            final_path.write_bytes(audio_bytes)
            wav_path.unlink(missing_ok=True)
            return str(final_path), audio_bytes

        return str(wav_path), audio_bytes

    def _convert_to_mp3(self, wav_bytes: bytes) -> bytes:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
        mp3_buf = io.BytesIO()
        audio.export(mp3_buf, format="mp3", bitrate="192k")
        return mp3_buf.getvalue()

    def synthesize_with_voice_profile(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        output_format: str = "wav",
    ) -> Tuple[str, bytes]:
        """Synthesize using a saved voice profile."""
        from backend.services.voice_manager import voice_manager

        profile = voice_manager.get_voice(voice_id)
        if not profile:
            raise ValueError(f"Voice profile '{voice_id}' not found")

        ref_audio = profile.get("reference_audio")
        ref_text = profile.get("reference_text")

        if not ref_audio or not Path(ref_audio).exists():
            raise FileNotFoundError(f"Reference audio not found for voice '{voice_id}'")

        return self.clone_voice(
            text=text,
            reference_audio_path=ref_audio,
            reference_text=ref_text,
            speed=speed,
            output_format=output_format,
        )


# Singleton
tts_engine = TTSEngine()
