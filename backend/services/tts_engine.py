"""
Voice Cloning TTS Engine using Fish Speech.

Fish Speech supports:
- Zero-shot voice cloning with 10-30s reference audio
- Fine-tuning with more data for higher quality
"""

import io
import uuid
import time
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Tuple

from backend.config import OUTPUT_DIR, SAMPLE_RATE


class TTSEngine:
    """Wrapper around Fish Speech for voice cloning inference."""

    def __init__(self):
        self._model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def _ensure_model(self):
        """Lazy-load Fish Speech model on first use."""
        if self._model is not None:
            return

        try:
            from fish_speech.models.vqgan.lit_module import VQGAN
            from fish_speech.models.text2semantic.llama import TextToSemantic
            print(f"Loading Fish Speech model on {self._device}...")
            # Fish Speech models will be loaded from HuggingFace cache
            self._model = True  # placeholder — real init below
            self._load_fish_speech()
            print("Fish Speech model loaded successfully.")
        except ImportError:
            print("Fish Speech not installed. Using subprocess fallback.")
            self._model = "cli"

    def _load_fish_speech(self):
        """Load Fish Speech models programmatically."""
        try:
            from tools.llama.generate import load_model as load_llama
            from tools.vqgan.inference import load_model as load_vqgan

            self._llama_model, self._llama_tokenizer = load_llama(
                checkpoint_path=None,  # auto-download
                device=self._device,
            )
            self._vqgan_model = load_vqgan(
                checkpoint_path=None,
                device=self._device,
            )
            self._model = "native"
        except Exception as e:
            print(f"Native loading failed ({e}), will use CLI fallback.")
            self._model = "cli"

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

        Args:
            text: Text to synthesize
            reference_audio_path: Path to reference audio (10-30s)
            reference_text: Transcript of reference audio (optional, improves quality)
            speed: Speaking speed multiplier
            output_format: "wav" or "mp3"

        Returns:
            (output_filepath, audio_bytes)
        """
        self._ensure_model()

        uid = uuid.uuid4().hex[:8]
        output_path = OUTPUT_DIR / f"clone_{uid}.{output_format}"

        start = time.time()

        if self._model == "cli":
            self._run_cli(text, reference_audio_path, reference_text, speed, output_path)
        else:
            self._run_native(text, reference_audio_path, reference_text, speed, output_path)

        elapsed = time.time() - start
        print(f"Voice cloning completed in {elapsed:.1f}s → {output_path.name}")

        audio_bytes = output_path.read_bytes()

        if output_format == "mp3":
            audio_bytes = self._convert_to_mp3(audio_bytes)
            mp3_path = output_path.with_suffix(".mp3")
            mp3_path.write_bytes(audio_bytes)
            output_path = mp3_path

        return str(output_path), audio_bytes

    def _run_cli(self, text, ref_audio, ref_text, speed, output_path):
        """Fallback: run Fish Speech via CLI subprocess."""
        import subprocess

        cmd = [
            "python", "-m", "fish_speech.tools.inference",
            "--text", text,
            "--reference_audio", ref_audio,
            "--output", str(output_path),
        ]
        if ref_text:
            cmd.extend(["--reference_text", ref_text])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(f"Fish Speech CLI failed:\n{proc.stderr}")

    def _run_native(self, text, ref_audio, ref_text, speed, output_path):
        """Run inference using loaded models directly."""
        # This will be filled in when Fish Speech Python API is available
        # For now, fall back to CLI
        self._run_cli(text, ref_audio, ref_text, speed, output_path)

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
        """
        Synthesize using a saved voice profile (trained or reference-based).
        """
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


# Singleton instance
tts_engine = TTSEngine()
