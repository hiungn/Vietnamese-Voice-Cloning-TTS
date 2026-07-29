from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.routers import clone, voices, recordings

app = FastAPI(
    title="Vietnamese Voice Cloning TTS",
    description="Clone any voice with just 10-30 seconds of audio",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(clone.router)
app.include_router(voices.router)
app.include_router(recordings.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files (built React app)
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
