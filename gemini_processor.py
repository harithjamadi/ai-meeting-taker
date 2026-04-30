import re
import time

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, logger
from processor_base import BaseProcessor

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class MeetingIntelligence(BaseProcessor):
    """Whisper (local) → Gemini text API."""

    def __init__(self):
        super().__init__()
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_id = GEMINI_MODEL
        logger.info(f"Gemini model: {self.model_id}")

    def _chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        cfg_kwargs = {
            "system_instruction": system,
            "max_output_tokens": max_tokens,
        }
        if json_mode:
            cfg_kwargs["response_mime_type"] = "application/json"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=user,
                    config=types.GenerateContentConfig(**cfg_kwargs),
                )
                return (response.text or "").strip()
            except Exception as e:
                logger.warning(f"Gemini call attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(self._parse_retry_delay(e))
        raise RuntimeError("Gemini call failed after multiple attempts.")

    @staticmethod
    def _parse_retry_delay(exc: Exception) -> float:
        match = re.search(r"retryDelay.*?(\d+)s", str(exc))
        return float(match.group(1)) + 2.0 if match else float(RETRY_BACKOFF_SECONDS)
