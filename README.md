---
title: Vietnamese Voice Cloning TTS
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
suggested_hardware: cpu-basic
pinned: false
license: apache-2.0
---

# Vietnamese Voice Cloning TTS

Clone any voice with just 10-30 seconds of audio. Record more sentences for higher quality.

## Features

- **Quick Clone**: Upload or record 10-30s of audio, enter text, get cloned speech
- **My Voices**: Save and manage voice profiles
- **Record**: Record multiple sentences to build a high-quality custom voice

## Tech Stack

- **Backend**: FastAPI + Fish Speech
- **Frontend**: React + TypeScript + shadcn/ui
- **Inference**: Fish Speech 1.5 (Apache 2.0)

## Local Development

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```
