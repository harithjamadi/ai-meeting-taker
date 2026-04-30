import torch
from pyannote.audio import Pipeline
from config import HF_TOKEN, logger, ENABLE_DIARIZATION

class DiarizationManager:
    """Handles speaker diarization using pyannote.audio."""

    def __init__(self):
        self.pipeline = None
        if ENABLE_DIARIZATION and HF_TOKEN:
            try:
                logger.info("Initializing Pyannote Diarization Pipeline (3.1)...")
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=HF_TOKEN
                )
                
                # Move to GPU if available (MPS for Mac, CUDA for Windows/Linux)
                if torch.backends.mps.is_available():
                    self.pipeline.to(torch.device("mps"))
                    logger.info("Diarization pipeline moved to Metal (MPS).")
                elif torch.cuda.is_available():
                    self.pipeline.to(torch.device("cuda"))
                    logger.info("Diarization pipeline moved to CUDA.")
                else:
                    logger.info("Diarization pipeline running on CPU.")
                    
            except Exception as e:
                logger.error(f"Failed to initialize diarization: {e}")
                logger.warning("Diarization will be skipped. Ensure you have accepted the model terms on Hugging Face.")
                self.pipeline = None

    def get_speakers(self, audio_path: str):
        """Identify speakers and their time segments."""
        if not self.pipeline:
            return None
            
        logger.info("Identifying speakers in audio...")
        try:
            diarization = self.pipeline(audio_path)
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
            return segments
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return None

def merge_transcript_with_speakers(transcript_segments, speaker_segments):
    """Align Whisper segments with Pyannote speaker labels."""
    if not speaker_segments:
        return "".join([s.text for s in transcript_segments])

    diarized_transcript = []
    
    for t_seg in transcript_segments:
        # Find the speaker that overlaps most with this transcript segment
        # Using the middle point of the transcript segment for simplicity
        mid_point = (t_seg.start + t_seg.end) / 2
        
        current_speaker = "Unknown"
        for s_seg in speaker_segments:
            if s_seg["start"] <= mid_point <= s_seg["end"]:
                current_speaker = s_seg["speaker"]
                break
        
        # Format as "Speaker 1: Text"
        # We can map "SPEAKER_00" to "Speaker 1" for readability
        speaker_id = current_speaker.replace("SPEAKER_", "Speaker ")
        diarized_transcript.append(f"{speaker_id}: {t_seg.text.strip()}")
        
    return "\n".join(diarized_transcript)
