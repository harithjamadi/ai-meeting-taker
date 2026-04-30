# AI Meeting Assistant (Obsidian Edition)

A local-first, privacy-focused meeting assistant that records audio, transcribes locally, and writes adaptive summaries into your Obsidian vault. Inspired by Notion AI Meeting Notes — but **air-gapped capable** and tunable to your voice.

---

## 🌟 What's New — Personality Update

The assistant no longer forces every conversation into a rigid `summary / decisions / action items` template. It now **adapts** like Notion AI does:

- **🎨 Meeting Styles** — Auto-detect, Team Meeting, Stand-up, 1:1, Sales Call, Interview, Brainstorm, Casual Conversation, Lecture. Each style has its own sections, voice, and JSON schema.
- **🗣️ Tone Control** — Professional, Friendly, Concise, Detailed, or Witty.
- **📏 Length Control** — Brief / Standard / Comprehensive.
- **🌐 Output Language** — English, Bahasa Malaysia, Japanese, Mandarin, Spanish, or auto-match the transcript.
- **📝 Custom Instructions** — Free-form: *"Skip pleasantries", "Add a glossary", "Focus on technical decisions"*.
- **📋 Pre-Meeting Context** — Inject an agenda or attendee list to ground accuracy.
- **👥 Speaker Name Mapping** — After diarization, the CLI asks you to map `Speaker 0 → Abdullah`, `Speaker 1 → John`.
- **🪄 Audience-Specific Recaps** — Post-process the meeting into a Slack message, follow-up email, executive summary, engineering recap, single tweet, or translated version. Recaps are appended to the same Obsidian file.
- **🪄 Auto-detect Style** — The "Auto" style classifies the transcript first, then routes to the right preset.
- **🧹 No more empty placeholders** — A casual chat won't get a forced "No action items recorded" block. Sections only render when they have real content.

Carried over: Speaker diarization (pyannote), Obsidian-style `[[bracket linking]]`, Faster-Whisper transcription, GGUF/Gemini/OpenRouter backends, YAML frontmatter, callouts, Dataview-ready dashboard.

---

## 🚀 How It Works

```
Mic + System Audio ──► WAV ──► Faster-Whisper (local) ──► [Style classify] ──► LLM (Llama.cpp / Gemini / OpenRouter) ──► Obsidian (.md)
                                       │
                                       └─► Diarization + Speaker name map ──┘
                                                                            │
                                                  ┌─ Recap loop ◄───────────┘
                                                  └─► Slack / Email / Exec / Engineering / Translation appended to file
```

---

## 📋 Requirements

- Python 3.13+
- [ffmpeg](https://ffmpeg.org/)
- [uv](https://github.com/astral-sh/uv)
- A GGUF model file (for the Llama.cpp backend, e.g. Mistral NeMo 12B)

---

## 🛠️ Setup

### 1. System dependencies
```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

### 2. Download a GGUF model
Place a GGUF file (e.g. [Mistral-NeMo-12B-v1-GGUF](https://huggingface.co/bartowski/Mistral-NeMo-12B-v1-GGUF)) under `models/`.

### 3. Python dependencies
```bash
uv sync
```

### 4. `.env` configuration
```env
# --- Backend models ---
LLAMA_CPP_MODEL_PATH=models/mistral-nemo-12b-v1.Q4_K_M.gguf
WHISPER_MODEL=base
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault/Meetings

# --- Optional cloud backends ---
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...

# --- Diarization ---
HF_TOKEN=...                       # Hugging Face token (accept pyannote terms first)
ENABLE_DIARIZATION=true

# --- Personality defaults (also pickable interactively at runtime) ---
MEETING_STYLE=auto                 # auto | team | standup | 1on1 | sales | interview | brainstorm | casual | lecture
MEETING_TONE=professional          # professional | friendly | concise | detailed | witty
MEETING_LENGTH=standard            # brief | standard | comprehensive
MEETING_LANGUAGE=auto              # auto | English | Bahasa Malaysia | Japanese | ...
MEETING_CUSTOM_INSTRUCTIONS=       # free-form, e.g. "Skip pleasantries"
OBSIDIAN_AUTO_LINK=true            # wrap names/projects in [[brackets]]
```

---

## ⌨️ Usage

```bash
uv run main.py
```

The CLI walks you through:

1. **Backend** — Llama.cpp (local) / Gemini / OpenRouter
2. **Meeting Style** — Auto, Team, Stand-up, 1:1, Sales, Interview, Brainstorm, Casual, Lecture
3. **Tone** — Professional / Friendly / Concise / Detailed / Witty
4. **Length** — Brief / Standard / Comprehensive
5. **Output Language**
6. **Custom Instructions** (optional)
7. **Pre-Meeting Context** (optional — agenda, attendees, project name)
8. Press **Enter** to record → **Enter** to stop
9. **Speaker Mapping** — After transcription, map `Speaker 0 → Abdullah`, etc.
10. **Recap Loop** — Append Slack / email / exec / engineering / translated recaps to the same file

Each chosen axis is recorded in the file's YAML frontmatter (`style`, `tone`, `language`) and tags (`style/standup`) so Dataview can filter or roll up by any of them.

---

## 🎨 Meeting Styles in Detail

| Style | Sections | Action Items | Decisions | Voice |
|---|---|---|---|---|
| **Auto** 🪄 | Chosen dynamically | If applicable | If applicable | Adapts to content |
| **Team Meeting** 👥 | Summary, Discussion Highlights, Open Questions | ✅ | ✅ | Professional, captures reasoning |
| **Stand-up** 🏃 | Yesterday, Today, Blockers | ✅ | ❌ | Terse, person-grouped |
| **1:1** 🤝 | Discussion, Feedback, Career & Growth | ✅ | ✅ | Warm, careful with sensitive topics |
| **Sales Call** 💼 | Customer Context, Needs, Objections, Buying Signals | ✅ | ✅ | Crisp, sales-savvy |
| **Interview** 🎤 | Background, Strengths, Concerns, Notable Quotes | ✅ | ❌ | Neutral, evidence-driven |
| **Brainstorm** 💡 | Theme, Ideas Generated, Promising Directions | ✅ | ❌ | Energetic, generous |
| **Casual** ☕ | What Was Discussed, Memorable Moments | ❌ | ❌ | Warm narrative — no corporate scaffolding |
| **Lecture** 🎓 | Topic, Key Concepts, Examples, Takeaways | ✅ | ❌ | Educational, restructured for learning |

---

## 🪄 Recap Presets

After analysis, choose one or many:

| Preset | Output |
|---|---|
| **Slack** | 2-4 sentence team update |
| **Email** | Subject + greeting + bullets + closing |
| **Exec** | 3-bullet outcomes / decisions / risks |
| **Engineering** | Technical decisions and blockers |
| **Tweet** | ≤280 chars |
| **Translate (Malay/Japanese)** | Section-preserving translation |
| **Custom** | Free-form prompt |

Each recap is appended to the original meeting `.md` so everything lives on one page.

---

## 📂 Project Structure

- `main.py` — CLI entry, interactive pickers, recap loop
- `audio_manager.py` — Cross-platform audio capture
- `processor_base.py` — Transcription, style classification, prompt assembly, JSON extraction
- `meeting_styles.py` — Style registry, tones, lengths, prompt builder
- `recap_generator.py` — Audience-specific recap presets
- `llama_cpp_processor.py` — Local GGUF backend (`_chat`)
- `gemini_processor.py` — Gemini cloud backend (`_chat`)
- `meeting_processor.py` — OpenRouter cloud backend (`_chat`)
- `diarization_manager.py` — pyannote speaker diarization
- `obsidian_exporter.py` — Markdown rendering with sections, callouts, recap append
- `config.py` — Pydantic models (`MeetingMinutes`, `Section`, `ActionItem`) and env loading

---

## 🛡️ Privacy

Designed to be **air-gapped capable**. Use the Llama.cpp backend and **no data leaves your machine** — transcription, diarization, and analysis all run on local hardware.
