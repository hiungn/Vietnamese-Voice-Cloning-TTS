from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
OUTPUT_DIR = DATA_DIR / "output"
VOICES_DIR = DATA_DIR / "voices"
SCRIPTS_DIR = DATA_DIR / "scripts"

# Ensure directories exist
for d in [RECORDINGS_DIR, OUTPUT_DIR, VOICES_DIR, SCRIPTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Fish Speech settings
FISH_SPEECH_MODEL = "fishaudio/fish-speech-1.5"
SAMPLE_RATE = 44100
DEFAULT_SPEED = 1.0

# Voice profile metadata file
VOICES_META = VOICES_DIR / "voices.json"

# Recording scripts
SCRIPTS_FILE = SCRIPTS_DIR / "scripts.json"
