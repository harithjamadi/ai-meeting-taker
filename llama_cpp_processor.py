import json
import os
from typing import Optional
from llama_cpp import Llama
from config import LLAMA_CPP_MODEL_PATH, logger, MeetingMinutes
from processor_base import BaseProcessor

class LlamaCppMeetingIntelligence(BaseProcessor):
    """Whisper (local) → Llama.cpp (Direct GGUF)."""

    def __init__(self):
        super().__init__()
        
        if not os.path.exists(LLAMA_CPP_MODEL_PATH):
            logger.error(f"GGUF model not found at: {LLAMA_CPP_MODEL_PATH}")
            raise FileNotFoundError(f"Please download a GGUF model and update LLAMA_CPP_MODEL_PATH in .env")

        logger.info(f"Initializing Llama.cpp with model: {LLAMA_CPP_MODEL_PATH}")
        
        # Initialize Llama.cpp
        # n_ctx: set to 32k for large transcripts
        # n_gpu_layers: -1 to offload everything to GPU (Metal on Mac, CUDA on Windows)
        self.llm = Llama(
            model_path=LLAMA_CPP_MODEL_PATH,
            n_ctx=32768,
            n_gpu_layers=-1,
            verbose=False
        )

        self.system_prompt = (
            "You are a professional meeting analyst. Generate a structured JSON response from "
            "the following meeting transcript. Be as detailed as possible.\n\n"
            "CRITICAL INSTRUCTION: Ignore background noise, game dialogue, video game characters "
            "(e.g., 'Ozzie', 'boats'), or unrelated conversational chatter. Focus ONLY on the "
            "professional, technical, or project-related discussion (e.g., 'MCP', 'development', 'tasks').\n\n"
            "Strictly adhere to this JSON schema:\n"
            "{\n"
            '  "title": "A concise and descriptive meeting title",\n'
            '  "date": "YYYY-MM-DD",\n'
            '  "summary": "A detailed multi-paragraph summary of the meeting",\n'
            '  "key_decisions": ["string"],\n'
            '  "action_items": [{"task": "string", "assignee": "string"}],\n'
            '  "topics": ["string"],\n'
            '  "sentiment": "Positive/Neutral/Negative"\n'
            "}\n"
            "Output ONLY valid JSON. No preamble, no conversational text."
        )

    def _analyse(self, transcript: str) -> dict:
        """Send transcript to Llama.cpp."""
        try:
            logger.info("Analysing transcript with Llama.cpp...")
            
            prompt = f"### System:\n{self.system_prompt}\n\n### User:\nTranscript:\n\n{transcript}\n\n### Assistant:\n"
            
            # Use JSON schema constrained generation if the GGUF model supports it via grammar.
            # For simplicity, we use regular completion and extract JSON.
            response = self.llm(
                prompt,
                max_tokens=4096,
                stop=["###", "\n\n\n"],
                echo=False
            )
            
            content = response["choices"][0]["text"].strip()
            
            # Basic JSON extraction in case of preamble (though we prompt against it)
            if "{" in content:
                content = content[content.find("{"):content.rfind("}")+1]
                
            return json.loads(content)

        except Exception as e:
            logger.error(f"Llama.cpp analysis failed: {e}")
            raise RuntimeError(f"Llama.cpp error: {e}")

    def process_audio(self, audio_path: str) -> Optional[MeetingMinutes]:
        """Main pipeline for Llama.cpp."""
        try:
            transcript = self.transcribe(audio_path)
            if not transcript:
                return None

            data = self._analyse(transcript)
            data["transcript"] = transcript
            
            return MeetingMinutes(**data)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None
