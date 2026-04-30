import json
import time
import urllib.request

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, logger
from processor_base import BaseProcessor

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 10


class MeetingIntelligence(BaseProcessor):
    """Whisper (local) → OpenRouter (remote chat completion)."""

    def __init__(self):
        super().__init__()
        logger.info(f"OpenRouter model: {OPENROUTER_MODEL}")

    def _chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        body = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        payload = json.dumps(body).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/ai-meeting-assistant",
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    "https://openrouter.ai/api/v1/chat/completions",
                    data=payload,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    response_body = json.loads(resp.read().decode())
                return response_body["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS)

        raise RuntimeError("OpenRouter call failed after multiple attempts.")
