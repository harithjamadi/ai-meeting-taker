# AI Meeting Assistant (Obsidian + Llama.cpp Edition)

A local-first, privacy-focused meeting recorder that transcribes audio locally and generates comprehensive summaries into your Obsidian vault using open-source models.

---

## 🌟 New in this Version

- **Llama.cpp Integration**: Use local GGUF models directly for 100% private analysis.
- **Obsidian Optimization**: Automatic export with YAML Properties and beautiful Callouts.
- **Faster-Whisper**: 4-8x faster transcription using `faster-whisper`.
- **Enhanced Detail**: Captures topics, sentiment, and structured action items.

---

## 🚀 How It Works

```
Microphone ──► WAV ──► Faster-Whisper (Local) ──► Mistral NeMo (Llama.cpp) ──► Obsidian (.md)
```

1. **Record**: Captures mic and system audio.
2. **Transcribe**: Converts audio to text using `faster-whisper` (on your GPU/CPU).
3. **Analyze**: Mistral NeMo (via Llama.cpp) summarizes the meeting.
4. **Export**: Saves a Markdown file with YAML frontmatter and Callouts to your Obsidian vault.

---

## 📋 Requirements

- Python 3.13+
- [ffmpeg](https://ffmpeg.org/) (Required for audio processing)
- [uv](https://github.com/astral-sh/uv) (Recommended package manager)
- A GGUF model file (e.g., Mistral NeMo 12B)

---

## 🛠️ Setup

### 1. Install System Dependencies
```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

### 2. Download a GGUF Model
Download a GGUF model from Hugging Face (e.g., [Mistral-NeMo-12B-v1-GGUF](https://huggingface.co/bartowski/Mistral-NeMo-12B-v1-GGUF)). Place it in a `models/` directory.

### 3. Install Python Dependencies
```bash
uv sync
```
*Note: This will compile llama-cpp-python for your hardware.*

### 4. Configuration
Create a `.env` file:
```env
LLAMA_CPP_MODEL_PATH=models/mistral-nemo-12b-v1.Q4_K_M.gguf
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault/Meetings
WHISPER_MODEL=base
```

---

## ⌨️ Usage

```bash
uv run main.py
```

1. Select **[1] Faster-Whisper + Llama.cpp**.
2. Press **Enter** to start recording.
3. Press **Enter** to stop.
4. Find your summarized meeting in your Obsidian vault!

---

## 📂 Project Structure

- `main.py`: Entry point and orchestration.
- `audio_manager.py`: Cross-platform audio recording.
- `llama_cpp_processor.py`: Local LLM analysis via Llama.cpp.
- `processor_base.py`: Faster-Whisper transcription logic.
- `obsidian_exporter.py`: Obsidian-specific Markdown formatting.
- `config.py`: Configuration and data models.

---

## 🛡️ Privacy
This app is designed to be **air-gapped capable**. If using the Llama.cpp backend, **no data ever leaves your machine**. Transcription and analysis are performed entirely on your local hardware.
