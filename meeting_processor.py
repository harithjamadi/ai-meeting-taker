import re
import time
import json
import urllib.request
from typing import Optional
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, logger, MeetingMinutes
from processor_base import BaseProcessor

MAX_RETRIES = 3

class MeetingIntelligence(BaseProcessor):
    """Whisper (local) → OpenRouter (Remote)."""

    def __init__(self):
        super().__init__()
        logger.info(f"OpenRouter model: {OPENROUTER_MODEL}")
        self.system_prompt = (
            "You are a professional meeting analyst. Generate a structured JSON response from "
            "the following meeting transcript. Strictly adhere to this schema:\n"
            "{\n"
            '  "title": "string",\n'
            '  "summary": "string",\n'
            '  "key_decisions": ["string"],\n'
            '  "action_items": [{"task": "string", "assignee": "string"}]\n'
            "}\n"
            "Output ONLY JSON, no conversational text."
        )

    def _analyse(self, transcript: str) -> dict:
        """Send transcript to OpenRouter."""
        payload = json.dumps({
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Transcript:\n\n{transcript}"},
            ],
            "response_format": {"type": "json_object"}
        }).encode()

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
                    body = json.loads(resp.read().decode())

                content = body["choices"][0]["message"]["content"].strip()
                return json.loads(content)

            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(10)

        raise RuntimeError("OpenRouter analysis failed after multiple attempts.")

    def process_audio(self, audio_path: str) -> Optional[MeetingMinutes]:
        """Main pipeline for OpenRouter."""
        try:
            transcript = self.transcribe(audio_path)
            if not transcript:
                return None

            logger.info("Sending transcript for OpenRouter analysis...")
            data = self._analyse(transcript)
            data["transcript"] = transcript
            
            return MeetingMinutes(**data)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None
