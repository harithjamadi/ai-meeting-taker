import platform
import soundcard as sc
import numpy as np
import soundfile as sf
import tempfile
import os
import threading
from datetime import datetime
from config import logger

# How long to wait (seconds) for each recording thread to stop cleanly.
THREAD_JOIN_TIMEOUT = 5.0

class CrossPlatformAudioRecorder:
    def __init__(self, samplerate=44100): # Standard CD quality
        self.fs = samplerate
        self.temp_file_path = None
        self.recording = False
        self.threads = []
        self.mic_buffer = []
        self.loopback_buffer = []

    def _get_devices(self):
        """Robust device discovery for Windows, macOS, and Linux."""
        system = platform.system()
        mic, loopback = None, None

        try:
            if system == "Windows":
                mic = sc.default_microphone()
                speaker = sc.default_speaker()
                loopback = sc.get_microphone(speaker.id, include_loopback=True)
            elif system == "Darwin": # macOS
                mics = sc.all_microphones()
                # 1. Look for the Aggregate Device first (Best for combined audio)
                for m in mics:
                    if "aggregate" in m.name.lower():
                        logger.info(f"Found Aggregate Device: {m.name}. Using as primary source.")
                        return m, None # Use only this device as it already combines mic + loopback

                # 2. Fallback to BlackHole/Others if no Aggregate Device is found
                for m in mics:
                    if any(x in m.name.lower() for x in ["blackhole", "vb-audio"]):
                        loopback = m
                        break
                mic = sc.default_microphone()
            else: # Linux
                mic = sc.default_microphone()
                logger.warning("Linux loopback capture requires manual PulseAudio setup.")
        except Exception as e:
            logger.error(f"Device discovery error: {e}")

        return mic, loopback

    def _record_stream(self, device, buffer_list: list, name: str):
        """Thread-safe stream recorder."""
        logger.debug(f"Starting {name} stream...")
        try:
            with device.recorder(samplerate=self.fs) as rec:
                while self.recording:
                    data = rec.record(numframes=self.fs // 10) # 100ms chunks
                    buffer_list.append(data.copy())
        except Exception as e:
            logger.error(f"Error in {name} stream: {e}")

    def start_recording(self):
        mic, loopback = self._get_devices()
        if not mic:
            raise RuntimeError("No microphone found. Please check your system settings.")

        self.recording = True
        self.mic_buffer, self.loopback_buffer = [], []
        self.threads = []

        # Start Mic Thread
        self.threads.append(threading.Thread(
            target=self._record_stream, args=(mic, self.mic_buffer, "Microphone"), daemon=True
        ))
        
        # Start Loopback Thread if available
        if loopback and loopback.id != mic.id:
            self.threads.append(threading.Thread(
                target=self._record_stream, args=(loopback, self.loopback_buffer, "System Audio"), daemon=True
            ))
        elif loopback:
            logger.info("Single device handles both mic and system audio (Aggregate Device).")

        for t in self.threads:
            t.start()

    def stop_recording(self) -> str | None:
        self.recording = False
        for t in self.threads:
            t.join(timeout=THREAD_JOIN_TIMEOUT)

        logger.info("Mixing and saving audio...")
        
        # Concatenate buffers
        m_audio = np.concatenate(self.mic_buffer) if self.mic_buffer else np.array([])
        l_audio = np.concatenate(self.loopback_buffer) if self.loopback_buffer else np.array([])

        if m_audio.size == 0 and l_audio.size == 0:
            return None

        # Normalize and Mix
        def to_2d(a): return a[:, np.newaxis] if a.ndim == 1 else a
        
        m_audio = to_2d(m_audio)
        l_audio = to_2d(l_audio)
        
        max_len = max(m_audio.shape[0], l_audio.shape[0])
        mixed = np.zeros((max_len, 2), dtype=np.float32) # Standard Stereo

        # Helper to add audio to mixed buffer
        def add_to_mixed(source, target):
            length = source.shape[0]
            if source.shape[1] == 1:
                target[:length, 0] += source[:, 0]
                target[:length, 1] += source[:, 0]
            else:
                target[:length, :] += source[:, :2]

        if m_audio.size: add_to_mixed(m_audio, mixed)
        if l_audio.size: add_to_mixed(l_audio, mixed)

        # Final normalization to avoid clipping
        peak = np.max(np.abs(mixed))
        if peak > 1.0: mixed /= peak

        # Save to a local debug folder instead of /tmp
        debug_dir = "debug_audio"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_file_path = os.path.join(debug_dir, f"recording_{timestamp}.wav")
        
        sf.write(self.temp_file_path, mixed, self.fs)
        
        return self.temp_file_path

    def cleanup(self):
        """No cleanup for now so user can check recordings."""
        if self.temp_file_path:
            logger.info(f"Temporary recording kept at: {os.path.abspath(self.temp_file_path)}")
