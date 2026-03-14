import re
import time
import json
from typing import Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, WHISPER_MODEL, logger, MeetingMinutes

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class MeetingIntelligence:
    """Whisper (local) → Gemini text API.

    Whisper transcribes the audio entirely on-device — no file upload, no
    audio quota consumed. Gemini then receives only the plain-text transcript,
    which costs a fraction of an audio request and never hits the Files API.
    """

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_id = GEMINI_MODEL
        logger.info(f"Gemini model: {self.model_id} | Whisper model: {WHISPER_MODEL}")
        self.system_instruction = (
            "You are an expert meeting analyst. You will be given a plain-text "
            "transcript of a meeting.\n"
            "Return a JSON object matching this schema exactly:\n"
            "{\n"
            '  "title": "A concise meeting title",\n'
            '  "summary": "A short paragraph summary",\n'
            '  "key_decisions": ["decision 1", "decision 2"],\n'
            '  "action_items": [{"task": "...", "assignee": "..."}]\n'
            "}\n"
            "Output ONLY the JSON — no markdown fences, no extra text."
        )

    # ------------------------------------------------------------------
    # Stage 1 — local Whisper transcription (no network, no quota)
    # ------------------------------------------------------------------

    def _transcribe(self, audio_path: str) -> str:
        try:
            import whisper
        except ImportError:
            raise RuntimeError(
                "openai-whisper is not installed. Run: uv add openai-whisper"
            )

        logger.info(f"Loading Whisper model '{WHISPER_MODEL}' (downloads on first use)…")
        model = whisper.load_model(WHISPER_MODEL)
        logger.info("Transcribing audio locally — this may take a moment…")
        result = model.transcribe(audio_path, fp16=False)
        transcript = result["text"].strip()
        logger.info(f"Transcription complete ({len(transcript)} chars).")
        return transcript

    # ------------------------------------------------------------------
    # Stage 2 — Gemini text analysis (one lightweight request)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_retry_delay(exc: Exception) -> float:
        match = re.search(r"retryDelay.*?(\d+)s", str(exc))
        return float(match.group(1)) + 2.0 if match else float(RETRY_BACKOFF_SECONDS)

    def _analyse(self, transcript: str) -> str:
        """Send transcript text to Gemini and return raw JSON string."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=f"Transcript:\n\n{transcript}",
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        response_mime_type="application/json",
                    ),
                )
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Analysis attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    delay = self._parse_retry_delay(e)
                    logger.info(f"Waiting {delay:.0f}s before retry…")
                    time.sleep(delay)
        raise RuntimeError(f"Gemini analysis failed after {MAX_RETRIES} attempts.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_audio(self, audio_path: str) -> Optional[MeetingMinutes]:
        # Step 1 — transcribe locally, zero quota used
        try:
            transcript = self._transcribe(audio_path)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

        # Step 2 — one text request to Gemini
        try:
            logger.info("Sending transcript to Gemini for analysis…")
            raw = self._analyse(transcript)
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)
            data["transcript"] = transcript
            minutes = MeetingMinutes(**data)
            logger.info("Meeting minutes generated successfully.")
            return minutes
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None