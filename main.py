import os
import re
from typing import Dict, Optional, Tuple

from audio_manager import CrossPlatformAudioRecorder
from config import (
    MEETING_CUSTOM_INSTRUCTIONS,
    MEETING_LANGUAGE,
    MEETING_LENGTH,
    MEETING_STYLE,
    MEETING_TONE,
    check_env,
    logger,
)
from meeting_styles import LENGTHS, STYLES, TONES
from obsidian_exporter import ObsidianExporter

BACKENDS = {
    "1": ("Faster-Whisper (Local) + Llama.cpp (Direct GGUF)", "llamacpp"),
    "2": ("Faster-Whisper (Local) + Gemini (Cloud)", "gemini"),
    "3": ("Faster-Whisper (Local) + OpenRouter (Cloud)", "openrouter"),
}

RECAP_OPTIONS = {
    "1": ("slack", "Slack-style update"),
    "2": ("email", "Follow-up email"),
    "3": ("exec", "Executive summary (3 bullets)"),
    "4": ("engineering", "Engineering recap"),
    "5": ("tweet", "Single tweet (≤280 chars)"),
    "6": ("translate-malay", "Translate to Bahasa Malaysia"),
    "7": ("translate-japanese", "Translate to Japanese"),
    "8": ("custom", "Custom instruction"),
}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_header():
    print("\n" + "═" * 60)
    print("        🎙️  AI MEETING ASSISTANT (PRO)        ")
    print("═" * 60)


# ─────────────────────────────────────────────────────────────────────
# Generic numeric picker
# ─────────────────────────────────────────────────────────────────────
def pick(title: str, items: Dict[str, str], default_key: str) -> str:
    """Render a numbered menu over a {key: label} dict and return the chosen key."""
    print(f"\n{title}")
    keys = list(items.keys())
    for i, key in enumerate(keys, 1):
        marker = "  (default)" if key == default_key else ""
        print(f"  [{i}] {items[key]}{marker}")
    while True:
        choice = input(f"\nChoice (Enter for default = {default_key}): ").strip()
        if not choice:
            return default_key
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                return keys[idx]
        if choice in keys:
            return choice
        print("⚠ Invalid choice — try again.")


# ─────────────────────────────────────────────────────────────────────
# Pickers for each axis
# ─────────────────────────────────────────────────────────────────────
def pick_backend() -> Tuple[str, str]:
    items = {k: v[0] for k, v in BACKENDS.items()}
    key = pick("Select Processing Backend:", items, "1")
    name, backend = BACKENDS[key]
    print(f"✔ Backend: {name}")
    return name, backend


def pick_style() -> str:
    items = {k: f"{s.icon} {s.name} — {s.description}" for k, s in STYLES.items()}
    key = pick("Select Meeting Style:", items, MEETING_STYLE if MEETING_STYLE in STYLES else "auto")
    print(f"✔ Style: {STYLES[key].name}")
    return key


def pick_tone() -> str:
    items = {k: f"{k.title()} — {desc}" for k, desc in TONES.items()}
    default = MEETING_TONE if MEETING_TONE in TONES else "professional"
    key = pick("Select Tone:", items, default)
    print(f"✔ Tone: {key}")
    return key


def pick_length() -> str:
    items = {k: f"{k.title()} — {desc}" for k, desc in LENGTHS.items()}
    default = MEETING_LENGTH if MEETING_LENGTH in LENGTHS else "standard"
    key = pick("Select Length:", items, default)
    print(f"✔ Length: {key}")
    return key


def pick_language() -> str:
    items = {
        "auto": "Auto — match the transcript",
        "English": "English",
        "Bahasa Malaysia": "Bahasa Malaysia",
        "Japanese": "Japanese (日本語)",
        "Mandarin Chinese": "Mandarin Chinese (中文)",
        "Spanish": "Spanish (Español)",
    }
    default = MEETING_LANGUAGE if MEETING_LANGUAGE in items else "auto"
    key = pick("Select Output Language:", items, default)
    print(f"✔ Language: {key}")
    return key


def get_custom_instructions() -> Optional[str]:
    print("\n📝 Custom Instructions (optional)")
    print('   e.g. "Skip pleasantries", "Focus on technical decisions", "Add a glossary section"')
    if MEETING_CUSTOM_INSTRUCTIONS:
        print(f"   Current default: {MEETING_CUSTOM_INSTRUCTIONS}")
    text = input("   Instructions (Enter to skip): ").strip()
    return text or MEETING_CUSTOM_INSTRUCTIONS


def get_pre_meeting_context() -> Optional[str]:
    print("\n📋 Pre-Meeting Context (optional)")
    print('   e.g. "Sprint planning for v2.0", "Interview for Senior PM role", "Weekly 1:1 with Sarah"')
    text = input("   Context (Enter to skip): ").strip()
    return text or None


def get_speaker_map(transcript: str) -> Optional[Dict[str, str]]:
    """If diarization labels are present in the transcript, ask user to map labels to real names."""
    labels = sorted(set(re.findall(r"Speaker \d+", transcript)))
    if not labels:
        return None
    print("\n👥 Speaker Mapping (optional — Enter to skip a label)")
    mapping: Dict[str, str] = {}
    for label in labels:
        name = input(f"   {label} = ").strip()
        if name:
            mapping[label] = name
    return mapping or None


def apply_speaker_map(transcript: str, mapping: Optional[Dict[str, str]]) -> str:
    if not mapping:
        return transcript
    out = transcript
    for label, name in mapping.items():
        out = out.replace(f"{label}:", f"{name}:")
    return out


# ─────────────────────────────────────────────────────────────────────
# Recap loop
# ─────────────────────────────────────────────────────────────────────
def post_meeting_recap_loop(processor, minutes, exporter: ObsidianExporter, md_path: str):
    while True:
        print("\n" + "─" * 60)
        print("Generate an audience-specific recap?")
        for k, (_, label) in RECAP_OPTIONS.items():
            print(f"  [{k}] {label}")
        print("  [0] Done")
        choice = input("\nChoice: ").strip()
        if choice in ("", "0"):
            break
        if choice not in RECAP_OPTIONS:
            print("⚠ Invalid")
            continue

        recap_key, label = RECAP_OPTIONS[choice]
        if recap_key == "custom":
            custom = input("   Enter custom recap instruction: ").strip()
            if not custom:
                continue
            recap_key = custom
            label = "Custom"

        print(f"\n⏳ Generating {label}...")
        recap = processor.generate_recap(minutes, recap_key)
        if not recap:
            print("⚠ Recap generation failed.")
            continue

        print("\n" + "─" * 60)
        print(recap)
        print("─" * 60)
        save = input("\nAppend to meeting file? [Y/n]: ").strip().lower()
        if save != "n":
            if exporter.append_recap(md_path, label, recap):
                print(f"✔ Appended to {md_path}")


# ─────────────────────────────────────────────────────────────────────
# Backend loader
# ─────────────────────────────────────────────────────────────────────
def load_processor(backend: str):
    if backend == "llamacpp":
        from llama_cpp_processor import LlamaCppMeetingIntelligence
        return LlamaCppMeetingIntelligence()
    if backend == "openrouter":
        from meeting_processor import MeetingIntelligence
        return MeetingIntelligence()
    if backend == "gemini":
        from gemini_processor import MeetingIntelligence
        return MeetingIntelligence()
    raise ValueError(f"Unknown backend: {backend}")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────
def main():
    clear_screen()
    show_header()

    # 1. Config selection
    _, backend_key = pick_backend()
    check_env(backend_key)

    style = pick_style()
    tone = pick_tone()
    length = pick_length()
    language = pick_language()
    custom_instructions = get_custom_instructions()
    pre_meeting_context = get_pre_meeting_context()

    # 2. Initialization
    try:
        processor = load_processor(backend_key)
        recorder = CrossPlatformAudioRecorder()
        exporter = ObsidianExporter()
        processor.configure(
            style=style,
            tone=tone,
            length=length,
            language=language,
            custom_instructions=custom_instructions,
            pre_meeting_context=pre_meeting_context,
        )
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # 3. Recording phase
    audio_path = None
    try:
        print("\n" + "─" * 60)
        input("👉 Press Enter to START recording... ")
        recorder.start_recording()
        print("🔴 RECORDING IN PROGRESS...")
        print("   (System audio and microphone are being captured)")
        input("👉 Press Enter to STOP recording...  ")
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user.")
    except Exception as e:
        logger.error(f"Recording error: {e}")
        return
    finally:
        audio_path = recorder.stop_recording()

    if not audio_path:
        logger.error("No audio captured.")
        return

    # 4. Transcribe + speaker map + analyse
    try:
        print("\n⏳ Transcribing locally...")
        transcript = processor.transcribe(audio_path)

        if not transcript or len(transcript.strip()) < 20:
            print("\n" + "!" * 60)
            print("⚠ NO SPEECH DETECTED")
            print("The recording was either silent or too short.")
            print(f"Check your mic and the audio file: {audio_path}")
            print("!" * 60 + "\n")
            return

        # Speaker mapping (only prompts if diarization labels are present)
        speaker_map = get_speaker_map(transcript)
        if speaker_map:
            transcript = apply_speaker_map(transcript, speaker_map)
            processor.configure(speaker_map=speaker_map)

        print("\n⏳ Analysing transcript...")
        minutes = processor.process_transcript(transcript)

        if not minutes:
            logger.error("Analysis returned no results.")
            return

        md_path = exporter.export_to_file(minutes)

        print("\n" + "═" * 60)
        print("             MEETING SUMMARY              ")
        print("─" * 60)
        print(f"📋 Title    : {minutes.title}")
        print(f"🎨 Style    : {minutes.style}  •  Tone: {minutes.tone}  •  Lang: {minutes.language}")
        if minutes.sections:
            print(f"📝 Sections : {len(minutes.sections)} ({', '.join(s.heading for s in minutes.sections)})")
        if minutes.key_decisions:
            print(f"🔑 Decisions: {len(minutes.key_decisions)}")
        if minutes.action_items:
            print(f"✅ Actions  : {len(minutes.action_items)} item(s)")
        if md_path:
            print(f"📄 File     : {os.path.abspath(md_path)}")
        print("═" * 60)

        # 5. Post-meeting recap loop
        if md_path:
            post_meeting_recap_loop(processor, minutes, exporter, md_path)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        recorder.cleanup()


if __name__ == "__main__":
    main()
