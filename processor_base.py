import json
import re
from abc import abstractmethod
from typing import Dict, List, Optional

from faster_whisper import WhisperModel

from config import (
    ENABLE_DIARIZATION,
    MEETING_CUSTOM_INSTRUCTIONS,
    MEETING_LANGUAGE,
    MEETING_LENGTH,
    MEETING_STYLE,
    MEETING_TONE,
    OBSIDIAN_AUTO_LINK,
    WHISPER_MODEL,
    MeetingMinutes,
    logger,
)
from diarization_manager import DiarizationManager, merge_transcript_with_speakers
from meeting_styles import STYLES, build_classify_prompt, build_system_prompt
from recap_generator import build_recap_prompt


class BaseProcessor:
    """Shared base. Owns transcription, style-aware prompt assembly, JSON
    extraction, auto-classification, and recap generation. Concrete subclasses
    just implement `_chat()` for their LLM backend."""

    def __init__(self):
        self._model = None
        self._diarizer = DiarizationManager() if ENABLE_DIARIZATION else None

        # Personality / output controls — overridable via configure()
        self.style: str = MEETING_STYLE
        self.tone: str = MEETING_TONE
        self.length: str = MEETING_LENGTH
        self.language: str = MEETING_LANGUAGE
        self.custom_instructions: Optional[str] = MEETING_CUSTOM_INSTRUCTIONS
        self.pre_meeting_context: Optional[str] = None
        self.speaker_map: Optional[Dict[str, str]] = None

    # ─────────────────────────────────────────────────────────────────
    # Configuration
    # ─────────────────────────────────────────────────────────────────
    def configure(
        self,
        *,
        style: Optional[str] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        language: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        pre_meeting_context: Optional[str] = None,
        speaker_map: Optional[Dict[str, str]] = None,
    ):
        if style is not None:               self.style = style
        if tone is not None:                self.tone = tone
        if length is not None:              self.length = length
        if language is not None:            self.language = language
        if custom_instructions is not None: self.custom_instructions = custom_instructions or None
        if pre_meeting_context is not None: self.pre_meeting_context = pre_meeting_context or None
        if speaker_map is not None:         self.speaker_map = speaker_map or None

    # ─────────────────────────────────────────────────────────────────
    # Transcription
    # ─────────────────────────────────────────────────────────────────
    def _get_model(self):
        if self._model is None:
            logger.info(f"Loading Faster-Whisper model '{WHISPER_MODEL}' (downloads on first use)...")
            self._model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio_path: str) -> str:
        try:
            model = self._get_model()
            logger.info("Transcribing audio locally — this may take a moment...")
            segments, info = model.transcribe(audio_path, beam_size=5)
            transcript_segments = list(segments)

            if self._diarizer:
                speaker_segments = self._diarizer.get_speakers(audio_path)
                if speaker_segments:
                    logger.info("Aligning transcript with speakers...")
                    transcript = merge_transcript_with_speakers(transcript_segments, speaker_segments)
                    logger.info(f"Diarized transcription complete ({len(transcript)} characters).")
                    return transcript

            transcript = "".join([s.text for s in transcript_segments]).strip()
            logger.info(f"Transcription complete ({len(transcript)} characters).")
            return transcript
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            raise RuntimeError(f"Transcription error: {e}")

    # ─────────────────────────────────────────────────────────────────
    # LLM (subclass implements)
    # ─────────────────────────────────────────────────────────────────
    @abstractmethod
    def _chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        """Single-turn LLM call. Returns raw text."""
        raise NotImplementedError

    # ─────────────────────────────────────────────────────────────────
    # Style classification
    # ─────────────────────────────────────────────────────────────────
    def classify_style(self, transcript: str) -> str:
        """Quick first-pass classifier when style is 'auto'."""
        try:
            excerpt = transcript[:4000]
            response = self._chat(
                build_classify_prompt(),
                excerpt,
                json_mode=False,
                max_tokens=20,
            ).strip().lower()
            for key in STYLES:
                if key == "auto":
                    continue
                if key in response:
                    return key
        except Exception as e:
            logger.warning(f"Style classification failed: {e}; defaulting to 'team'")
        return "team"

    # ─────────────────────────────────────────────────────────────────
    # JSON extraction
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _extract_json(raw: str) -> dict:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        if "{" in cleaned:
            cleaned = cleaned[cleaned.find("{"):cleaned.rfind("}") + 1]
        return json.loads(cleaned)

    # ─────────────────────────────────────────────────────────────────
    # Analysis pipeline
    # ─────────────────────────────────────────────────────────────────
    def _analyse(self, transcript: str) -> dict:
        effective_style = self.style
        if effective_style == "auto":
            effective_style = self.classify_style(transcript)
            logger.info(f"Auto-detected meeting style: {effective_style}")

        system = build_system_prompt(
            style_key=effective_style,
            tone_key=self.tone,
            length_key=self.length,
            language=self.language,
            custom_instructions=self.custom_instructions,
            pre_meeting_context=self.pre_meeting_context,
            speaker_map=self.speaker_map,
            obsidian_linking=OBSIDIAN_AUTO_LINK,
        )

        raw = self._chat(
            system=system,
            user=f"Transcript:\n\n{transcript}",
            json_mode=True,
            max_tokens=4096,
        )
        data = self._extract_json(raw)
        data["style"] = effective_style
        return data

    def process_transcript(self, transcript: str) -> Optional[MeetingMinutes]:
        if not transcript or len(transcript.strip()) < 20:
            return None
        try:
            data = self._analyse(transcript)
            data["transcript"] = transcript
            data["tone"] = self.tone
            data["custom_instructions"] = self.custom_instructions
            return MeetingMinutes(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model JSON: {e}")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
        return None

    def process_audio(self, audio_path: str) -> Optional[MeetingMinutes]:
        try:
            transcript = self.transcribe(audio_path)
            return self.process_transcript(transcript)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────
    # Recap (post-processing)
    # ─────────────────────────────────────────────────────────────────
    def generate_recap(self, minutes: MeetingMinutes, recap_type: str) -> Optional[str]:
        from obsidian_exporter import ObsidianExporter
        try:
            markdown = ObsidianExporter().render_markdown(minutes)
            prompt = build_recap_prompt(recap_type, markdown, minutes.transcript or "")
            return self._chat(
                system="You are a helpful AI assistant that produces clean recaps.",
                user=prompt,
                json_mode=False,
                max_tokens=1500,
            ).strip()
        except Exception as e:
            logger.error(f"Recap generation failed: {e}")
            return None
