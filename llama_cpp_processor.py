import os

from llama_cpp import Llama

from config import LLAMA_CPP_MODEL_PATH, logger
from processor_base import BaseProcessor


class LlamaCppMeetingIntelligence(BaseProcessor):
    """Whisper (local) → Llama.cpp (Direct GGUF). Style/tone/length and prompt
    composition are handled in BaseProcessor; this subclass only owns the LLM call."""

    def __init__(self):
        super().__init__()

        if not os.path.exists(LLAMA_CPP_MODEL_PATH):
            logger.error(f"GGUF model not found at: {LLAMA_CPP_MODEL_PATH}")
            raise FileNotFoundError("Please download a GGUF model and update LLAMA_CPP_MODEL_PATH in .env")

        logger.info(f"Initializing Llama.cpp with model: {LLAMA_CPP_MODEL_PATH}")
        self.llm = Llama(
            model_path=LLAMA_CPP_MODEL_PATH,
            n_ctx=32768,
            n_gpu_layers=-1,
            verbose=False,
        )

    def _chat(
        self,
        system: str,
        user: str,
        json_mode: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        prompt = (
            f"### System:\n{system}\n\n"
            f"### User:\n{user}\n\n"
            f"### Assistant:\n"
        )
        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            stop=["###", "\n\n\n"],
            echo=False,
        )
        return response["choices"][0]["text"].strip()
