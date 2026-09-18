import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
AUDIO_CACHE_DIR = BASE_DIR / "audio_cache"
DB_PATH = DATA_DIR / "jarvis_memory.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("JARVIS_HOST", "127.0.0.1")
PORT = int(os.getenv("JARVIS_PORT", "8765"))

# Default voice settings (Edge TTS)
# en-GB-RyanNeural has a classic British Jarvis tone
TTS_VOICE = os.getenv("JARVIS_TTS_VOICE", "en-GB-RyanNeural")
TTS_VOICE_ID = os.getenv("JARVIS_TTS_VOICE_ID", "id-ID-ArdiNeural")

# Fail safe settings
FAILSAFE_ENABLED = True
KEYSTROKE_MIN_INTERVAL = 0.02
KEYSTROKE_MAX_INTERVAL = 0.06
