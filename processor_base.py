from faster_whisper import WhisperModel
from typing import Optional
from config import WHISPER_MODEL, logger

class BaseProcessor:
    """Shared base for all processors, providing robust local transcription."""
    
    def __init__(self):
        self._model = None

    def _get_model(self):
        """Lazy-loads the Whisper model to save memory."""
        if self._model is None:
            logger.info(f"Loading Faster-Whisper model '{WHISPER_MODEL}' (downloads on first use)...")
            # Use 'cpu' or 'cuda' depending on hardware; defaulting to 'cpu' for safety but can be optimized.
            # Using int8 quantization for speed/memory efficiency.
            self._model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio to plain text using local Faster-Whisper."""
        try:
            model = self._get_model()
            logger.info("Transcribing audio locally — this may take a moment...")
            
            # segments is an iterable; joining them into a single string.
            segments, info = model.transcribe(audio_path, beam_size=5)
            
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text)
            
            transcript = "".join(transcript_parts).strip()
            logger.info(f"Transcription complete ({len(transcript)} characters).")
            return transcript
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            raise RuntimeError(f"Transcription error: {e}")
