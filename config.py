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

# Llama.cpp & Obsidian Config
# Path to your GGUF model file (e.g., ./models/mistral-nemo-12b-v1.Q4_K_M.gguf)
LLAMA_CPP_MODEL_PATH = os.getenv("LLAMA_CPP_MODEL_PATH", "models/mistral-nemo.gguf")
OBSIDIAN_VAULT_PATH  = os.getenv("OBSIDIAN_VAULT_PATH",  "meeting-content")

# Production Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("AI-Meeting-Assistant")


class ActionItem(BaseModel):
    task: str
    assignee: str


class MeetingMinutes(BaseModel):
    title: str = Field(..., description="The generated title of the meeting")
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), description="Date of the meeting")
    summary: str = Field(..., description="A concise summary of the meeting")
    transcript: Optional[str] = Field(None, description="Full raw transcript of the meeting")
    key_decisions: List[str] = Field(default_factory=list, description="List of key decisions made")
    action_items: List[ActionItem] = Field(default_factory=list, description="List of tasks and assignees")
    topics: List[str] = Field(default_factory=list, description="Main topics discussed during the meeting")
    sentiment: str = Field("Neutral", description="General sentiment of the meeting")


def check_env(backend: str):
    """Validate only the keys required for the chosen backend."""
    missing = []
    if backend == "gemini" and not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if backend == "openrouter" and not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if backend == "ollama":
        # Ollama is local, no key needed but we can check if it's reachable later
        pass
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please add them to your .env file.")
        sys.exit(1)
    logger.info("Environment validated.")