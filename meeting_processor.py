import json
import time
import re
import urllib.request
from typing import Optional
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, WHISPER_MODEL, logger, MeetingMinutes

# Free model on OpenRouter — strong enough for meeting analysis.
# Full list of free models: https://openrouter.ai/models?q=free
# Model is configured via OPENROUTER_MODEL in .env

# How many times to retry a transient API failure.
MAX_RETRIES = 3


class MeetingIntelligence:
    def __init__(self):
        logger.info(f"OpenRouter model: {OPENROUTER_MODEL} | Whisper model: {WHISPER_MODEL}")

    """Two-stage pipeline:

    1. Transcribe  — Whisper runs locally (offline, free, no quota).
    2. Analyse     — OpenRouter sends the transcript text to a free LLM.
    """

    # ------------------------------------------------------------------
    # Stage 1 — local Whisper transcription
    # ------------------------------------------------------------------

    def _transcribe(self, audio_path: str) -> str:
        """Return a plain-text transcript of *audio_path* using Whisper."""
        try:
            import whisper  # openai-whisper package
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
    # Stage 2 — OpenRouter analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_retry_delay(exc: Exception) -> float:
        """Extract the suggested retry delay from a 429 error body, if present."""
        match = re.search(r"retryDelay.*?(\d+)s", str(exc))
        return float(match.group(1)) + 2.0 if match else 10.0

    def _analyse(self, transcript: str) -> dict:
        """Send *transcript* to OpenRouter and return a parsed minutes dict."""
        system_prompt = (
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

        payload = json.dumps({
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n\n{transcript}"},
            ],
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

                text = body["choices"][0]["message"]["content"].strip()
                # Strip accidental markdown fences
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
                return json.loads(text)

            except Exception as e:
                logger.warning(f"Analysis attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    delay = self._parse_retry_delay(e)
                    logger.info(f"Waiting {delay:.0f}s before retry…")
                    time.sleep(delay)

        raise RuntimeError(f"Analysis failed after {MAX_RETRIES} attempts.")

    # ------------------------------------------------------------------
    # Public API  (same signature as the old GeminiProcessor)
    # ------------------------------------------------------------------

    def process_audio(self, audio_path: str) -> Optional[MeetingMinutes]:
        """Transcribe *audio_path* then analyse the transcript.

        Returns a MeetingMinutes instance, or None on failure.
        """
        try:
            transcript = self._transcribe(audio_path)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

        try:
            logger.info("Sending transcript to OpenRouter for analysis…")
            data = self._analyse(transcript)
            data["transcript"] = transcript   # attach the raw transcript
            minutes = MeetingMinutes(**data)
            logger.info("Meeting minutes generated successfully.")
            return minutes
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None