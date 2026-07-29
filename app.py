"""
Vietnamese Voice Cloning TTS — Gradio App for HuggingFace Spaces (ZeroGPU)
"""

import os
import uuid
import time
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

import numpy as np
import soundfile as sf
import gradio as gr

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
DATA_DIR = Path("data")
OUTPUT_DIR = DATA_DIR / "output"
VOICES_DIR = DATA_DIR / "voices"
VOICES_META = VOICES_DIR / "voices.json"

for d in [OUTPUT_DIR, VOICES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# ZeroGPU decorator (only works on HF Spaces, no-op locally)
# ---------------------------------------------------------------------------
try:
    import spaces
    GPU = spaces.GPU
except (ImportError, Exception):
    # Running locally without ZeroGPU — just pass through
    def GPU(fn=None, **kwargs):
        if fn is not None:
            return fn
        def decorator(f):
            return f
        return decorator

# ---------------------------------------------------------------------------
# Voice profile helpers
# ---------------------------------------------------------------------------
def _load_voices() -> dict:
    if VOICES_META.exists():
        return json.loads(VOICES_META.read_text(encoding="utf-8"))
    return {}

def _save_voices(data: dict):
    VOICES_META.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _get_voice_choices() -> list[str]:
    voices = _load_voices()
    return [f"{v['name']} ({vid[:8]})" for vid, v in voices.items()]

def _voice_choice_to_id(choice: str) -> str:
    voices = _load_voices()
    for vid in voices:
        if vid[:8] in choice:
            return vid
    return ""

# ---------------------------------------------------------------------------
# TTS Inference (runs on GPU via ZeroGPU)
# ---------------------------------------------------------------------------
@GPU(duration=120)
def clone_voice(ref_audio_path: str, ref_text: str, target_text: str) -> str:
    """Run Fish Speech voice cloning inference."""
    import torch

    uid = uuid.uuid4().hex[:8]
    output_path = OUTPUT_DIR / f"clone_{uid}.wav"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    start = time.time()

    # Try fish_speech Python API first
    try:
        from fish_speech.inference import inference
        inference(
            text=target_text,
            reference_audio=ref_audio_path,
            reference_text=ref_text if ref_text else None,
            output_path=str(output_path),
            device=device,
        )
    except (ImportError, Exception):
        # Fallback to CLI
        cmd = [
            "python", "-m", "fish_speech.inference",
            "--text", target_text,
            "--reference_audio", ref_audio_path,
            "--output", str(output_path),
            "--device", device,
        ]
        if ref_text:
            cmd.extend(["--reference_text", ref_text])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            raise gr.Error(f"Inference failed: {proc.stderr[:500]}")

    elapsed = time.time() - start
    print(f"Clone completed in {elapsed:.1f}s on {device}")

    if not output_path.exists():
        raise gr.Error("Output audio was not generated. Check Fish Speech installation.")

    return str(output_path)


# ---------------------------------------------------------------------------
# Tab 1: Voice Clone
# ---------------------------------------------------------------------------
def handle_clone(ref_audio, ref_text, target_text, save_name):
    """Handle the clone button click."""
    if ref_audio is None:
        raise gr.Error("Please upload or record reference audio (10-30 seconds).")
    if not target_text or not target_text.strip():
        raise gr.Error("Please enter the text you want the cloned voice to say.")

    # ref_audio is a filepath from Gradio
    output_path = clone_voice(ref_audio, ref_text or "", target_text.strip())

    # Optionally save as voice profile
    status_msg = ""
    if save_name and save_name.strip():
        voice_id = uuid.uuid4().hex[:12]
        voice_dir = VOICES_DIR / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        dest = voice_dir / "reference.wav"
        shutil.copy2(ref_audio, str(dest))

        from pydub import AudioSegment
        audio = AudioSegment.from_file(ref_audio)
        duration_sec = len(audio) / 1000.0

        voices = _load_voices()
        voices[voice_id] = {
            "name": save_name.strip(),
            "type": "reference",
            "reference_audio": str(dest),
            "reference_text": ref_text or "",
            "duration_sec": round(duration_sec, 1),
            "created_at": datetime.now().isoformat(),
        }
        _save_voices(voices)
        status_msg = f"Voice '{save_name.strip()}' saved!"

    return output_path, status_msg


def handle_clone_with_saved(voice_choice, target_text):
    """Clone using a saved voice profile."""
    if not voice_choice:
        raise gr.Error("Please select a saved voice.")
    if not target_text or not target_text.strip():
        raise gr.Error("Please enter text to speak.")

    voice_id = _voice_choice_to_id(voice_choice)
    voices = _load_voices()
    profile = voices.get(voice_id)
    if not profile:
        raise gr.Error("Voice profile not found.")

    ref_audio = profile["reference_audio"]
    ref_text = profile.get("reference_text", "")

    if not Path(ref_audio).exists():
        raise gr.Error("Reference audio file missing. Please re-create the voice.")

    output_path = clone_voice(ref_audio, ref_text, target_text.strip())
    return output_path


# ---------------------------------------------------------------------------
# Tab 2: My Voices
# ---------------------------------------------------------------------------
def get_voices_table():
    voices = _load_voices()
    if not voices:
        return "No saved voices yet. Clone a voice and check 'Save as voice profile' to save it."
    rows = []
    for vid, v in voices.items():
        rows.append(
            f"**{v['name']}** — {v.get('duration_sec', '?')}s — "
            f"Created {v.get('created_at', 'unknown')[:10]} — ID: `{vid[:8]}`"
        )
    return "\n\n".join(rows)


def delete_voice_by_choice(choice):
    if not choice:
        return "Select a voice to delete.", gr.update(choices=_get_voice_choices())
    voice_id = _voice_choice_to_id(choice)
    voices = _load_voices()
    if voice_id in voices:
        voice_dir = VOICES_DIR / voice_id
        if voice_dir.exists():
            shutil.rmtree(voice_dir)
        del voices[voice_id]
        _save_voices(voices)
        return f"Deleted.", gr.update(choices=_get_voice_choices(), value=None)
    return "Voice not found.", gr.update(choices=_get_voice_choices())


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
).set(
    button_primary_background_fill="*primary_500",
    button_primary_text_color="white",
    block_label_text_size="sm",
)

# ---------------------------------------------------------------------------
# Build Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(theme=theme, title="Vietnamese Voice Cloning") as demo:
    gr.Markdown(
        """
        # 🎙️ Vietnamese Voice Cloning
        **Clone any voice with just 10-30 seconds of audio.**
        Upload or record a reference voice, type your text, and get instant voice cloning.
        """
    )

    with gr.Tabs():
        # ===================== TAB 1: CLONE =====================
        with gr.TabItem("🔊 Voice Clone", id="clone"):
            with gr.Row():
                # Left column: inputs
                with gr.Column(scale=3):
                    gr.Markdown("### Reference Audio")
                    ref_audio = gr.Audio(
                        label="Upload or record 10-30s of the voice to clone",
                        type="filepath",
                        sources=["upload", "microphone"],
                    )
                    ref_text = gr.Textbox(
                        label="Reference text (optional — what the audio says)",
                        placeholder="Transcript of the reference audio...",
                        lines=2,
                    )

                    gr.Markdown("### Text to Speak")
                    target_text = gr.Textbox(
                        label="Enter the text for the cloned voice to say",
                        placeholder="Nhap van ban muon chuyen thanh giong noi...",
                        lines=5,
                    )

                    with gr.Accordion("Save as voice profile", open=False):
                        save_name = gr.Textbox(
                            label="Voice name",
                            placeholder="e.g. My Voice, Narrator...",
                        )

                    clone_btn = gr.Button(
                        "🎤 Clone Voice",
                        variant="primary",
                        size="lg",
                    )

                # Right column: output
                with gr.Column(scale=2):
                    gr.Markdown("### Result")
                    output_audio = gr.Audio(label="Cloned audio", type="filepath")
                    save_status = gr.Textbox(label="Status", interactive=False, visible=True)

            clone_btn.click(
                fn=handle_clone,
                inputs=[ref_audio, ref_text, target_text, save_name],
                outputs=[output_audio, save_status],
            )

            # --- Use saved voice ---
            gr.Markdown("---")
            gr.Markdown("### Or use a saved voice")
            with gr.Row():
                with gr.Column(scale=3):
                    saved_voice_dropdown = gr.Dropdown(
                        label="Saved voices",
                        choices=_get_voice_choices(),
                        interactive=True,
                    )
                    saved_text = gr.Textbox(
                        label="Text to speak",
                        placeholder="Nhap van ban...",
                        lines=3,
                    )
                    saved_clone_btn = gr.Button("🔊 Clone with Saved Voice", variant="secondary")
                with gr.Column(scale=2):
                    saved_output = gr.Audio(label="Result", type="filepath")

            saved_clone_btn.click(
                fn=handle_clone_with_saved,
                inputs=[saved_voice_dropdown, saved_text],
                outputs=[saved_output],
            )

        # ===================== TAB 2: MY VOICES =====================
        with gr.TabItem("📚 My Voices", id="voices"):
            gr.Markdown("### Saved Voice Profiles")
            voices_display = gr.Markdown(get_voices_table())
            refresh_btn = gr.Button("🔄 Refresh", size="sm")
            refresh_btn.click(fn=get_voices_table, outputs=[voices_display])

            gr.Markdown("### Delete a Voice")
            with gr.Row():
                del_dropdown = gr.Dropdown(
                    label="Select voice",
                    choices=_get_voice_choices(),
                    interactive=True,
                )
                del_btn = gr.Button("🗑️ Delete", variant="stop", size="sm")
                del_status = gr.Textbox(label="Status", interactive=False)

            del_btn.click(
                fn=delete_voice_by_choice,
                inputs=[del_dropdown],
                outputs=[del_status, del_dropdown],
            ).then(fn=get_voices_table, outputs=[voices_display])

    # Refresh saved voice dropdowns when tabs change
    demo.load(fn=lambda: gr.update(choices=_get_voice_choices()), outputs=[saved_voice_dropdown])

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
