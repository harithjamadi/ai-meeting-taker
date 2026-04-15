import sys
import os
from config import logger, check_env
from audio_manager import CrossPlatformAudioRecorder
from obsidian_exporter import ObsidianExporter

BACKENDS = {
    "1": ("Faster-Whisper (Local) + Llama.cpp (Direct GGUF)", "llamacpp"),
    "2": ("Faster-Whisper (Local) + Gemini (Cloud)", "gemini"),
    "3": ("Faster-Whisper (Local) + OpenRouter (Cloud)", "openrouter"),
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    print("\n" + "═"*50)
    print("      🎙️  AI MEETING ASSISTANT (PRO)      ")
    print("═"*50)

def pick_backend() -> tuple[str, str]:
    """Interactive backend selection."""
    print("\nSelect Processing Backend:")
    for key, (name, _) in BACKENDS.items():
        print(f"  [{key}] {name}")

    while True:
        choice = input("\nChoice (default 1): ").strip() or "1"
        if choice in BACKENDS:
            name, backend = BACKENDS[choice]
            print(f"✔ Using: {name}")
            return name, backend
        print(f"⚠ Invalid choice '{choice}', please enter 1, 2, or 3.")

def load_processor(backend: str):
    """Import and return the correct processor for *backend*."""
    if backend == "llamacpp":
        from llama_cpp_processor import LlamaCppMeetingIntelligence
        return LlamaCppMeetingIntelligence()
    elif backend == "openrouter":
        from meeting_processor import MeetingIntelligence
        return MeetingIntelligence()
    elif backend == "gemini":
        from gemini_processor import MeetingIntelligence
        return MeetingIntelligence()
    raise ValueError(f"Unknown backend: {backend}")

def main():
    clear_screen()
    show_header()

    # 1. Config selection
    backend_name, backend_key = pick_backend()
    check_env(backend_key)

    # 2. Initialization
    try:
        processor = load_processor(backend_key)
        recorder = CrossPlatformAudioRecorder()
        # Default to Obsidian exporter
        exporter = ObsidianExporter()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    # 3. Recording Phase
    audio_path = None
    try:
        print("\n" + "─"*50)
        input("👉 Press Enter to START recording... ")
        recorder.start_recording()
        print("🔴 RECORDING IN PROGRESS...")
        print("   (System audio and Microphone are being captured)")
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

    # 4. Processing Phase
    try:
        print(f"\n⏳ Processing... (Local transcription + AI Analysis)")
        print(f"DEBUG: Audio saved at {audio_path}")

        # 1. Transcribe first to check content
        transcript = processor.transcribe(audio_path)

        if not transcript or len(transcript.strip()) < 20:
            print("\n" + "!"*50)
            print("⚠ NO SPEECH DETECTED")
            print("The recording was either silent or too short.")
            print(f"Check your mic and the audio file: {audio_path}")
            print("!"*50 + "\n")
            return

        # 2. Analyze
        # We pass the audio path, but process_audio in the backend will re-transcribe for now
        # (This is slightly redundant but safer for this phase)
        minutes = processor.process_audio(audio_path)

        if minutes:
            # Save to Markdown (Obsidian)
            report_path = exporter.export_to_file(minutes)
            
            print("\n" + "═"*50)
            print("             MEETING SUMMARY              ")
            print("─"*50)
            print(f"📋 Title   : {minutes.title}")
            print(f"📝 Summary : {minutes.summary[:150]}...")
            print(f"✅ Actions : {len(minutes.action_items)} item(s)")
            print(f"📄 File    : {os.path.abspath(report_path)}")
            print("═"*50 + "\n")
        else:
            logger.error("Analysis returned no results.")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main()
