# AI Meeting Assistant

A local-first, open-source meeting recorder that automatically transcribes audio and generates structured meeting minutes using AI.

Audio is transcribed on-device with [Whisper](https://github.com/openai/whisper) — no audio ever leaves your machine. Only the plain-text transcript is sent to the AI backend of your choice for analysis.

---

## Features

- 🎙️ Records microphone (and system audio on Windows / macOS with BlackHole)
- 🔒 Local transcription via Whisper — audio stays on your machine
- 🤖 Choice of AI backend for analysis: OpenRouter (free) or Gemini
- 📝 Exports structured meeting minutes as Markdown files
- ✅ Captures title, summary, key decisions, action items, and full transcript
- 🔁 Automatic retry with correct backoff on rate-limit errors

---

## How It Works

```
Microphone ──► WAV file ──► Whisper (local) ──► Transcript text ──► AI backend ──► Minutes .md
```

1. **Record** — captures mic audio into a temporary WAV file
2. **Transcribe** — Whisper runs entirely on your CPU/GPU, no API call
3. **Analyse** — transcript text is sent to your chosen backend (OpenRouter or Gemini)
4. **Export** — structured minutes are saved to `meeting-content/`

---

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [ffmpeg](https://ffmpeg.org/) (required by Whisper)

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
winget install ffmpeg
```

---

## Installation

```bash
git clone https://github.com/your-username/ai-meeting-taker
cd ai-meeting-taker

# Install Python dependencies
uv add openai-whisper soundcard soundfile numpy pydantic python-dotenv

# For the Gemini backend (optional)
uv add google-genai
```

---

## Configuration

Copy the example below into a `.env` file in the project root:

```env
# --- Whisper (local transcription) ---
WHISPER_MODEL=base          # tiny | base | small | medium | large

# --- OpenRouter backend ---
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# --- Gemini backend ---
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash
```

Only the key for the backend you intend to use needs to be set. The app validates this at startup and exits cleanly if a required key is missing.

### Whisper model sizes

| Model  | Size    | Speed  | Accuracy |
|--------|---------|--------|----------|
| tiny   | ~75 MB  | Fast   | Lower    |
| base   | ~140 MB | Fast   | Good     |
| small  | ~460 MB | Medium | Better   |
| medium | ~1.5 GB | Slow   | Best     |

`base` is the default and works well for clear meeting audio.

### AI backend comparison

| | Whisper + OpenRouter | Whisper + Gemini |
|---|---|---|
| Cost | Free | Free tier / paid |
| Audio uploaded | Never | Never |
| Analysis quality | Good (Llama 3.3 70B) | Better (Gemini Flash) |
| Rate limits | 20 req/min free tier | Per-day free tier limit |
| Requires SDK | No (stdlib only) | Yes (`google-genai`) |

---

## Usage

```bash
uv run main.py
```

You will be prompted to choose a backend before recording starts:

```
╔══════════════════════════════════╗
║   AI Meeting Assistant (FOSS)    ║
╚══════════════════════════════════╝

Select processing backend:
  [1] Whisper + OpenRouter
  [2] Whisper + Gemini

Enter choice (default 1):
```

Then:

1. Press **Enter** to start recording
2. Press **Enter** again to stop
3. Whisper transcribes the audio locally
4. The transcript is analysed by the chosen backend
5. Minutes are saved to `meeting-content/` as a `.md` file

---

## Output

Each meeting is saved as a Markdown file in `meeting-content/`:

```
meeting-content/
└── Q3 Budget Review - 2026-03-14 10-23.md
```

The file includes:

```markdown
# Q3 Budget Review

**Date:** 2026-03-14 10:23

## Summary
...

## Key Decisions
- ...

## Action Items
- [ ] **Alice** — Send revised forecast by Friday

---

## Full Transcript
...
```

---

## System Audio Capture (Optional)

By default only your microphone is recorded. To also capture system audio (e.g. remote participants in a call):

**macOS** — Install [BlackHole](https://existential.audio/blackhole/) and create a Multi-Output Aggregate Device in Audio MIDI Setup that combines your microphone and BlackHole. The app will detect it automatically.

**Windows** — Works out of the box via WASAPI loopback. No setup needed.

**Linux** — Not supported automatically. Configure a PulseAudio monitor source manually.

---

## Project Structure

```
├── main.py               # Entry point, backend selector, recording loop
├── audio_manager.py      # Cross-platform audio capture and WAV mixing
├── gemini_processor.py   # Whisper → Gemini pipeline
├── meeting_processor.py  # Whisper → OpenRouter pipeline
├── file_exporter.py      # Markdown export
├── config.py             # Env vars, Pydantic models, logging
└── meeting-content/      # Output directory (auto-created)
```

---

## Troubleshooting

**`No such file or directory: 'ffmpeg'`**
Whisper requires ffmpeg to decode audio. Install it with `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Linux).

**`429 RESOURCE_EXHAUSTED` on Gemini**
You've hit the free tier daily limit. The app will wait the suggested retry delay and try again automatically. If it keeps failing, switch to OpenRouter (`[1]`) or upgrade your Gemini API plan.

**`No Aggregate/BlackHole device found`**
System audio capture is optional. The app records microphone-only and continues normally. See the System Audio Capture section above to enable it.

**Minutes file not created**
Check the logs for an error from the AI backend. The transcript is still captured in memory — if analysis fails, you can re-run the app and it will re-transcribe.