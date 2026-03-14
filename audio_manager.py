import platform
import soundcard as sc
import numpy as np
import soundfile as sf
import tempfile
import os
import threading
from config import logger

# How long to wait (seconds) for each recording thread to stop cleanly.
THREAD_JOIN_TIMEOUT = 5.0


class CrossPlatformAudioRecorder:
    def __init__(self, samplerate=48000):
        self.fs = samplerate
        self.temp_file_path = None
        self.recording = False
        self.threads = []
        self.mic_buffer = []
        self.loopback_buffer = []
        # Flag: True when mic and loopback are the same physical device (e.g.
        # a macOS Aggregate Device).  In that case the single mic stream already
        # contains both sides, so we skip a second recording thread.
        self._single_stream = False

    # ------------------------------------------------------------------
    # Device discovery
    # ------------------------------------------------------------------

    def _get_devices(self):
        """Return (mic, loopback) device handles for the current platform.

        Returns (None, None) if no suitable devices can be found, after
        logging an appropriate warning so the caller can surface it.
        """
        system = platform.system()
        mic = None
        loopback = None

        if system == "Windows":
            try:
                mic = sc.default_microphone()
                speaker = sc.default_speaker()
                loopback = sc.get_microphone(speaker.id, include_loopback=True)
                logger.info("Using default Windows devices.")
            except Exception as e:
                logger.error(f"Error getting default Windows devices: {e}")

        elif system == "Darwin":
            try:
                mics = sc.all_microphones()
                for m in mics:
                    if "aggregate" in m.name.lower() or "blackhole" in m.name.lower():
                        loopback = m
                        break
                mic = sc.default_microphone()
                if loopback is None:
                    logger.warning(
                        "No Aggregate/BlackHole device found on macOS. "
                        "System audio will NOT be captured. "
                        "Install BlackHole and create an Aggregate Device to fix this."
                    )
                logger.info("Using macOS devices.")
            except Exception as e:
                logger.error(f"Error getting macOS devices: {e}")

        else:
            # Linux — loopback capture typically requires PulseAudio monitor
            # source; for now we record mic only and warn the user.
            try:
                mic = sc.default_microphone()
                logger.warning(
                    "Linux detected. System audio (loopback) capture is not "
                    "supported automatically. Only microphone will be recorded. "
                    "Configure a PulseAudio monitor source for full capture."
                )
            except Exception as e:
                logger.error(f"Error getting Linux microphone: {e}")

        if mic is None:
            logger.error("No microphone found. Cannot record.")

        return mic, loopback

    # ------------------------------------------------------------------
    # Recording threads
    # ------------------------------------------------------------------

    def _record_stream(self, device, buffer_list: list, name: str = "Unknown"):
        logger.info(f"Opening stream on device: {name} at {self.fs} Hz")
        try:
            with device.recorder(samplerate=self.fs) as rec:
                while self.recording:
                    data = rec.record(numframes=4800)  # ~0.1 s chunks
                    buffer_list.append(data.copy())
        except Exception as e:
            logger.error(f"Failed to record from device '{name}': {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_recording(self):
        mic, loopback = self._get_devices()

        if mic is None:
            raise RuntimeError("No microphone available — cannot start recording.")

        self.recording = True
        self.mic_buffer = []
        self.loopback_buffer = []
        self._single_stream = False
        self.threads = []

        logger.info(
            f"Starting recording... "
            f"(Mic: {mic.name}, Loopback: {loopback.name if loopback else 'None'})"
        )

        self.threads.append(
            threading.Thread(
                target=self._record_stream,
                args=(mic, self.mic_buffer, f"Mic-{mic.name}"),
                daemon=True,
            )
        )

        if loopback is not None:
            if mic.id == loopback.id:
                # Aggregate / BlackHole device — single stream covers both sides.
                self._single_stream = True
                logger.info(
                    "Mic and loopback share the same device — "
                    "capturing as a single combined stream."
                )
            else:
                self.threads.append(
                    threading.Thread(
                        target=self._record_stream,
                        args=(loopback, self.loopback_buffer, f"Loopback-{loopback.name}"),
                        daemon=True,
                    )
                )

        for t in self.threads:
            t.start()

    def stop_recording(self) -> str | None:
        """Stop all recording threads and mix the captured buffers.

        Returns the path to a temporary WAV file, or None if no audio was
        captured.
        """
        self.recording = False

        for t in self.threads:
            t.join(timeout=THREAD_JOIN_TIMEOUT)
            if t.is_alive():
                logger.warning(
                    f"Recording thread '{t.name}' did not stop within "
                    f"{THREAD_JOIN_TIMEOUT}s — it may still be running."
                )

        logger.info("Recording stopped. Mixing streams…")

        # When the devices were the same physical unit, all audio landed in
        # mic_buffer; nothing in loopback_buffer.
        m_audio = np.concatenate(self.mic_buffer) if self.mic_buffer else np.array([])
        l_audio = np.concatenate(self.loopback_buffer) if self.loopback_buffer else np.array([])

        if m_audio.size == 0 and l_audio.size == 0:
            logger.error("No audio data captured.")
            return None

        # --- normalise to 2-D (frames, channels) -------------------------
        def to_2d(audio):
            if audio.ndim == 1:
                return audio[:, np.newaxis]
            return audio

        m_audio = to_2d(m_audio) if m_audio.size else m_audio
        l_audio = to_2d(l_audio) if l_audio.size else l_audio

        m_ch = m_audio.shape[1] if m_audio.size else 0
        l_ch = l_audio.shape[1] if l_audio.size else 0
        target_ch = max(2, m_ch, l_ch)

        max_len = max(
            m_audio.shape[0] if m_audio.size else 0,
            l_audio.shape[0] if l_audio.size else 0,
        )

        mixed = np.zeros((max_len, target_ch), dtype=np.float32)

        if m_audio.size:
            # Expand mono → stereo by repeating the single channel.
            # After tiling, m_audio has target_ch columns — write ALL of them.
            if m_ch < target_ch:
                m_audio = np.tile(m_audio, (1, target_ch // m_ch))
            mixed[: m_audio.shape[0], :] += m_audio

        if l_audio.size:
            if l_ch < target_ch:
                l_audio = np.tile(l_audio, (1, target_ch // l_ch))
            mixed[: l_audio.shape[0], :] += l_audio

        # Normalise to prevent clipping
        peak = np.max(np.abs(mixed))
        if peak > 1.0:
            mixed /= peak

        temp_fd, self.temp_file_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)
        sf.write(self.temp_file_path, mixed, self.fs)
        logger.info(f"Saved temporary audio to {self.temp_file_path}")
        return self.temp_file_path

    def cleanup(self):
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
            logger.info("Cleaned up temporary audio file.")
            self.temp_file_path = None