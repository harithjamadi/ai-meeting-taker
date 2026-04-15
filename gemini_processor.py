import re
import time
import json
from typing import Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, logger, MeetingMinutes
from processor_base import BaseProcessor

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5

class MeetingIntelligence(BaseProcessor):
    """Whisper (local) → Gemini text API (Lite)."""

    def __init__(self):
        super().__init__()
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_id = GEMINI_MODEL
        logger.info(f"Gemini model: {self.model_id}")
        self.system_instruction = (
            "You are a professional meeting analyst. You will be provided with a transcript. "
            "Generate a highly accurate JSON document including a descriptive title, a concise "
            "summary of discussions, a list of key decisions, and actionable items with assignees. "
            "Format your response as pure JSON matching this schema:\n"
            "{\n"
            '  "title": "string",\n'
            '  "summary": "string",\n'
            '  "key_decisions": ["string"],\n'
            '  "action_items": [{"task": "string", "assignee": "string"}]\n'
            "}"
        )

    def _analyse(self, transcript: str) -> str:
        """Send transcript to Gemini for structured analysis."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=f"Transcript of the meeting:\n\n{transcript}",
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        response_mime_type="application/json",
                    ),
                )
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini analysis attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    delay = self._parse_retry_delay(e)
                    time.sleep(delay)
        raise RuntimeError("Gemini analysis failed after multiple attempts.")

    @staticmethod
    def _parse_retry_delay(exc: Exception) -> float:
        match = re.search(r"retryDelay.*?(\d+)s", str(exc))
        return float(match.group(1)) + 2.0 if match else float(RETRY_BACKOFF_SECONDS)

    def process_audio(self, audio_path: str) -> Optional[MeetingMinutes]:
        """Main pipeline: Local transcription → Cloud analysis."""
        try:
            transcript = self.transcribe(audio_path)
            if not transcript:
                logger.error("Empty transcript generated.")
                return None

            logger.info("Sending transcript for analysis...")
            raw_response = self._analyse(transcript)
            
            # Clean possible markdown formatting
            raw_response = re.sub(r"^```(?:json)?\s*", "", raw_response)
            raw_response = re.sub(r"\s*```$", "", raw_response)
            
            data = json.loads(raw_response)
            data["transcript"] = transcript
            
            minutes = MeetingMinutes(**data)
            logger.info("Analysis complete and validated.")
            return minutes

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model response: {e}")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
        return None
