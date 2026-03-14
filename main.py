import sys
from config import logger, check_env
from audio_manager import CrossPlatformAudioRecorder
from file_exporter import FileExporter

BACKENDS = {
    "1": ("Whisper + OpenRouter", "openrouter"),
    "2": ("Whisper + Gemini",     "gemini"),
}


def pick_backend() -> tuple[str, str]:
    """Show a menu and return (display_name, backend_key)."""
    print("\n╔══════════════════════════════════╗")
    print("║   AI Meeting Assistant (FOSS)    ║")
    print("╚══════════════════════════════════╝")
    print("\nSelect processing backend:")
    for key, (name, _) in BACKENDS.items():
        print(f"  [{key}] {name}")

    while True:
        choice = input("\nEnter choice (default 1): ").strip() or "1"
        if choice in BACKENDS:
            name, backend = BACKENDS[choice]
            print(f"✔  Using: {name}")
            return name, backend
        print(f"  ⚠  Invalid choice '{choice}', please enter 1 or 2.")


def load_processor(backend: str):
    """Import and return the correct processor for *backend*."""
    if backend == "openrouter":
        from meeting_processor import MeetingIntelligence
        return MeetingIntelligence()
    elif backend == "gemini":
        from gemini_processor import MeetingIntelligence
        return MeetingIntelligence()
    raise ValueError(f"Unknown backend: {backend}")


def main():
    # 1. Pick backend before touching any API keys
    backend_name, backend_key = pick_backend()

    # 2. Validate only the relevant env var
    check_env(backend_key)

    # 3. Lazy-load the processor (avoids importing unused dependencies)
    processor = load_processor(backend_key)

    recorder = CrossPlatformAudioRecorder()
    exporter = FileExporter()
    audio_path = None

    # 4. Record
    try:
        input("\nPress Enter to START recording…  ")
        recorder.start_recording()
        input("🔴 Recording… Press Enter to STOP.  ")
    except KeyboardInterrupt:
        print("\n⚠  Recording interrupted by user.")
    except RuntimeError as e:
        logger.error(f"Could not start recording: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error during capture: {e}")
    finally:
        try:
            audio_path = recorder.stop_recording()
        except Exception as e:
            logger.error(f"Error while stopping recording: {e}")
            audio_path = None

    if not audio_path:
        logger.error("No audio was captured — nothing to process.")
        return

    # 5. Process
    try:
        print(f"\n⏳ Processing with {backend_name}…")
        minutes = processor.process_audio(audio_path)

        if minutes:
            exporter.export_to_file(minutes)
            print("\n─── Meeting Minutes ─────────────────")
            print(f"📋 Title   : {minutes.title}")
            print(f"📝 Summary : {minutes.summary}")
            if minutes.action_items:
                print(f"✅ Actions : {len(minutes.action_items)} item(s) captured")
            print("─────────────────────────────────────")
        else:
            logger.error("Failed to generate meeting minutes.")

    except KeyboardInterrupt:
        print("\n⚠  Processing interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
    finally:
        recorder.cleanup()


if __name__ == "__main__":
    main()