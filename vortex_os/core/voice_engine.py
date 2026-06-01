# core/voice_engine.py
# VORTEX OS - Voice Engine
# Handles speech recognition and text-to-speech.
#
# Architecture:
# - VoiceEngine runs in a background thread (never blocks GUI)
# - Emits signals when speech is recognized
# - TTS runs in a separate daemon thread so it never blocks input
# - The GUI and terminal connect to signals to receive transcribed text

import os
import threading
import json

from PyQt6.QtCore import QObject, pyqtSignal


class VoiceEngine(QObject):
    """
    Central voice I/O manager for VORTEX OS.

    Signals:
        speech_recognized(str) : fired when microphone captures speech
        listening_started      : fired when mic opens
        listening_stopped      : fired when mic closes
        tts_started            : fired when TTS begins speaking
        tts_finished           : fired when TTS finishes
        error_occurred(str)    : fired on any voice error
    """

    speech_recognized  = pyqtSignal(str)
    listening_started  = pyqtSignal()
    listening_stopped  = pyqtSignal()
    tts_started        = pyqtSignal()
    tts_finished       = pyqtSignal()
    error_occurred     = pyqtSignal(str)

    def __init__(self, config_path="config/voice_config.json"):
        super().__init__()

        self._config       = self._load_config(config_path)
        self._listening    = False
        self._tts_engine   = None
        self._listen_thread= None

        # Initialize TTS engine
        self._init_tts()

    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                "language":           "en-US",
                "tts_rate":           165,
                "tts_volume":         0.9,
                "tts_voice_index":    0,
                "speak_responses":    True,
                "speak_max_chars":    400,
            }

    def _init_tts(self):
        """
        Initializes the pyttsx3 text-to-speech engine.

        pyttsx3 works offline — no internet needed for TTS.
        It uses the system's built-in speech synthesizer:
        - Linux   : espeak or espeak-ng
        - Windows : SAPI5
        - macOS   : NSSpeechSynthesizer
        """
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()

            # Apply config settings
            self._tts_engine.setProperty(
                'rate',
                self._config.get("tts_rate", 165)
            )
            self._tts_engine.setProperty(
                'volume',
                self._config.get("tts_volume", 0.9)
            )

            # Select voice by index
            voices = self._tts_engine.getProperty('voices')
            voice_idx = self._config.get("tts_voice_index", 0)
            if voices and voice_idx < len(voices):
                self._tts_engine.setProperty(
                    'voice', voices[voice_idx].id
                )

        except ImportError:
            self.error_occurred.emit(
                "pyttsx3 not installed. Run: pip3 install pyttsx3"
            )
        except Exception as e:
            self.error_occurred.emit(f"TTS init error: {e}")

    # ─────────────────────────────────────────────
    #  TEXT TO SPEECH
    # ─────────────────────────────────────────────

    def speak(self, text):
        """
        Speaks text aloud in a background thread.
        Non-blocking — returns immediately.

        Why a new thread each time?
        pyttsx3's runAndWait() blocks until speech finishes.
        Running it in a daemon thread keeps the GUI responsive.
        """
        if not self._config.get("speak_responses", True):
            return

        if not self._tts_engine:
            return

        # Truncate very long responses
        max_chars = self._config.get("speak_max_chars", 400)
        if len(text) > max_chars:
            text = text[:max_chars] + "... and more."

        # Remove markdown-style backticks and symbols
        text = self._clean_for_speech(text)

        def _do_speak():
            try:
                self.tts_started.emit()
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
                self.tts_finished.emit()
            except Exception as e:
                self.error_occurred.emit(f"TTS error: {e}")

        thread = threading.Thread(target=_do_speak, daemon=True)
        thread.start()

    def _clean_for_speech(self, text):
        """
        Removes markdown and symbols that sound bad when spoken.
        For example: `vault list` → vault list
        """
        import re
        # Remove backticks
        text = text.replace('`', '')
        # Remove bullet points
        text = re.sub(r'^\s*[•·\-\*]\s*', '', text, flags=re.MULTILINE)
        # Remove multiple newlines
        text = re.sub(r'\n+', '. ', text)
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def stop_speaking(self):
        """Stops any current TTS output."""
        try:
            if self._tts_engine:
                self._tts_engine.stop()
        except Exception:
            pass

    # ─────────────────────────────────────────────
    #  SPEECH RECOGNITION
    # ─────────────────────────────────────────────

    def listen_once(self):
     """
    Listens for one phrase from the microphone.
    Runs recognition in background thread.
    Uses a direct callback instead of signals to avoid
    cross-thread signal delivery issues.
    """
     if self._listening:
        return

     thread = threading.Thread(
        target=self._do_listen_once,
        daemon=True
     )
     thread.start()
    def _do_listen_once(self):
     """
    Runs in background thread.
    Uses QTimer.singleShot to deliver results to main thread
    instead of signals — more reliable for cross-thread delivery.
    """
     try:
        import speech_recognition as sr
     except ImportError:
        self._deliver_error(
            "SpeechRecognition not installed.\n"
            "Run: pip3 install SpeechRecognition"
        )
        return

     self._listening = True

    # Notify main thread that listening started
     from PyQt6.QtCore import QTimer
     QTimer.singleShot(0, self.listening_started.emit)

     recognizer                          = sr.Recognizer()
     recognizer.energy_threshold         = 300
     recognizer.dynamic_energy_threshold = False
     recognizer.pause_threshold          = 0.8

     mic_index = self._config.get("microphone_index", 0)

     try:
        with sr.Microphone(device_index=mic_index) as source:
            print("  [Voice] Listening — speak now...")
            try:
                audio = recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=15
                )
                print("  [Voice] Audio captured, transcribing...")
            except sr.WaitTimeoutError:
                self._listening = False
                QTimer.singleShot(0, self.listening_stopped.emit)
                self._deliver_error(
                    "No speech detected.\n"
                    "Speak louder or closer to the microphone."
                )
                return

     except Exception as e:
        self._listening = False
        QTimer.singleShot(0, self.listening_stopped.emit)
        self._deliver_error(f"Microphone error: {e}")
        return

     self._listening = False
     QTimer.singleShot(0, self.listening_stopped.emit)

     lang = self._config.get("language", "en-US")

     try:
        text = recognizer.recognize_google(audio, language=lang)
        print(f"  [Voice] Recognized: '{text}'")

        # Deliver to main thread via QTimer instead of signal
        # This bypasses cross-thread signal delivery completely
        self._deliver_speech(text)

     except sr.UnknownValueError:
        self._deliver_error(
            "Could not understand speech.\n"
            "Please speak clearly and try again."
        )
     except sr.RequestError as e:
        self._deliver_error(
            f"Google Speech API error: {e}\n"
            f"Check your internet connection."
        )


    def _deliver_speech(self, text):
     """
    Delivers recognized speech to the main thread.
    QTimer.singleShot is one of the very few Qt functions
    that is truly safe to call from any thread.
    It posts a callback to the main event loop directly.
     """
     from PyQt6.QtCore import QTimer
     QTimer.singleShot(0, lambda: self.speech_recognized.emit(text))


    def _deliver_error(self, msg):
     """
    Delivers an error message to the main thread.
    Same mechanism as _deliver_speech.
    """
     from PyQt6.QtCore import QTimer
     QTimer.singleShot(0, lambda: self.error_occurred.emit(msg))
    
    def start_continuous_listening(self, callback):
        """
        Starts continuous background listening.
        Calls callback(text) each time speech is recognized.
        Runs until stop_continuous_listening() is called.

        Used by voice command mode — listens continuously
        for VORTEX commands or ARIA questions.
        """
        if self._listening:
            return

        self._continuous = True
        self._listen_thread = threading.Thread(
            target=self._continuous_loop,
            args=(callback,),
            daemon=True
        )
        self._listen_thread.start()

    def _continuous_loop(self, callback):
     """Continuous listening loop — no auto-calibration."""
     try:
        import speech_recognition as sr
     except ImportError:
        self.error_occurred.emit("SpeechRecognition not installed.")
        return

     recognizer = sr.Recognizer()
     recognizer.energy_threshold         = 300
     recognizer.dynamic_energy_threshold = False
     recognizer.pause_threshold          = 0.8

     lang      = self._config.get("language", "en-US")
     mic_index = self._config.get("microphone_index", 0)

     self._listening = True
     self.listening_started.emit()

     with sr.Microphone(device_index=mic_index) as source:
        # NO adjust_for_ambient_noise here
        while self._continuous:
            try:
                audio = recognizer.listen(
                    source,
                    timeout=2,
                    phrase_time_limit=12
                )
                try:
                    text = recognizer.recognize_google(
                        audio, language=lang
                    )
                    if text.strip():
                        callback(text.strip())
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    pass

            except sr.WaitTimeoutError:
                pass

     self._listening = False
     self.listening_stopped.emit()

    def stop_continuous_listening(self):
        """Stops the continuous listening loop."""
        self._continuous = False
        self._listening  = False


# ── Global singleton ──────────────────────────────────────

_voice_engine = None


def get_voice_engine():
    """Returns the global VoiceEngine instance."""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceEngine()
    return _voice_engine