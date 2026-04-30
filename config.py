import sys
import os
import logging
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# API keys — only the one for the chosen backend needs to be set
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")

# Whisper model size: tiny | base | small | medium | large
WHISPER_MODEL      = os.getenv("WHISPER_MODEL",      "base")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL",   "meta-llama/llama-3.3-70b-instruct:free")
GEMINI_MODEL       = os.getenv("GEMINI_MODEL",        "gemini-1.5-flash")

# --- Hugging Face (Faster-Whisper & Diarization) ---
HF_TOKEN = os.getenv("HF_TOKEN")

# Llama.cpp & Obsidian Config
LLAMA_CPP_MODEL_PATH = os.getenv("LLAMA_CPP_MODEL_PATH", "models/mistral-nemo.gguf")
OBSIDIAN_VAULT_PATH  = os.getenv("OBSIDIAN_VAULT_PATH",  "meeting-content")

# Feature Flags
ENABLE_DIARIZATION = os.getenv("ENABLE_DIARIZATION", "true").lower() == "true"
OBSIDIAN_AUTO_LINK = os.getenv("OBSIDIAN_AUTO_LINK", "true").lower() == "true"

# --- Personality / output controls ---
# Defaults are used when the interactive picker is skipped or env is non-interactive.
MEETING_STYLE                = os.getenv("MEETING_STYLE",                "auto")
MEETING_TONE                 = os.getenv("MEETING_TONE",                 "professional")
MEETING_LENGTH               = os.getenv("MEETING_LENGTH",               "standard")
MEETING_LANGUAGE             = os.getenv("MEETING_LANGUAGE",             "auto")
MEETING_CUSTOM_INSTRUCTIONS  = os.getenv("MEETING_CUSTOM_INSTRUCTIONS",  "") or None

# Production Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("AI-Meeting-Assistant")


class Section(BaseModel):
    """A single section of the meeting summary. Sections are flexible and chosen
    per meeting style — they replace the old fixed 'summary / decisions' template."""
    heading: str
    body: str
    icon: Optional[str] = Field(default=None, description="Obsidian callout icon (abstract, info, tip, warning, quote, ...)")


class ActionItem(BaseModel):
    task: str
    assignee: str = ""
    due: Optional[str] = None
    priority: Optional[str] = None  # high | medium | low


class MeetingMinutes(BaseModel):
    """Flexible meeting output. Sections drive the document body; action_items
    and key_decisions are optional and only filled when the chosen style supports them."""
    title: str = Field(..., description="Generated descriptive title")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    # personality fingerprint
    style: str = "auto"
    tone: str = "professional"
    language: str = "en"

    # body
    sections: List[Section] = Field(default_factory=list)

    # optional structured data (style-dependent)
    key_decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    sentiment: str = "Neutral"

    # raw + provenance
    transcript: Optional[str] = None
    custom_instructions: Optional[str] = None


def check_env(backend: str):
    """Validate only the keys required for the chosen backend."""
    missing = []
    if backend == "gemini" and not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if backend == "openrouter" and not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if ENABLE_DIARIZATION and not HF_TOKEN:
        logger.warning("ENABLE_DIARIZATION is True but HF_TOKEN is missing. Diarization will be disabled.")

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please add them to your .env file.")
        sys.exit(1)
    logger.info("Environment validated.")
