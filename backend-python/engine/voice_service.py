import asyncio
import os
import uuid
import re
import threading
import time
from pathlib import Path
from typing import Optional, Callable
import edge_tts
import pygame

try:
    import speech_recognition as sr
except ImportError:
    sr = None

from config import AUDIO_CACHE_DIR, TTS_VOICE, TTS_VOICE_ID

# Wake word variations (including typo tolerance: jarvis, jarvius, javis, jarviz)
WAKE_WORD_REGEX = re.compile(r"\b(jarvis|jarvius|javis|jarviz)\b", re.IGNORECASE)

class VoiceService:
    def __init__(self):
        pygame.mixer.init()
        self.default_voice_en = TTS_VOICE
        self.default_voice_id = TTS_VOICE_ID
        self.recognizer = sr.Recognizer() if sr else None
        if self.recognizer:
            # Exactly 5.0 seconds of non-speaking audio before considering speech phrase complete
            self.recognizer.pause_threshold = 5.0
            self.recognizer.non_speaking_duration = 0.8
            self.recognizer.energy_threshold = 400
            self.recognizer.dynamic_energy_threshold = True

        self._stop_listening_fn = None
        self._is_listening = False
        self._awaiting_command = False
        self._awaiting_command_timestamp = 0.0

    def set_awaiting_command(self, active: bool):
        self._awaiting_command = active
        self._awaiting_command_timestamp = time.time() if active else 0.0

    def is_awaiting_command(self) -> bool:
        if self._awaiting_command and (time.time() - self._awaiting_command_timestamp < 45.0):
            return True
        self._awaiting_command = False
        return False

    def _detect_voice(self, text: str) -> str:
        id_words = [
            "selamat", "tolong", "buka", "cari", "siap", "terima kasih", "halo", "sore",
            "pagi", "malam", "bagaimana", "cuaca", "tutup", "jalankan", "ketik", "buat",
            "matikan", "volume", "layar", "bantu", "bisa", "apa", "kabar", "kamu", "saya",
            "ada", "iya", "ya"
        ]
        lower = text.lower()
        if any(re.search(rf"\b{w}\b", lower) for w in id_words):
            return self.default_voice_id
        return self.default_voice_en

    async def generate_speech(self, text: str, voice: Optional[str] = None, play_locally: bool = True) -> Path:
        """
        Generates TTS audio file using Edge-TTS and optionally plays it locally.
        Returns the Path to the generated MP3 file.
        """
        selected_voice = voice or self._detect_voice(text)
        filename = f"tts_{uuid.uuid4().hex[:10]}.mp3"
        output_path = AUDIO_CACHE_DIR / filename

        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(str(output_path))

        if play_locally:
            self.play_audio_file(output_path)

        return output_path

    def play_audio_file(self, audio_path: Path):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[VoiceService] Local playback error: {e}")

    def stop_playback(self):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception as e:
            print(f"[VoiceService] Stop playback error: {e}")

    def get_greeting(self, user_name: str = "Sir") -> str:
        import datetime
        hour = datetime.datetime.now().hour
        if 4 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        else:
            period = "evening"
        return f"System online. Good {period}, {user_name}. All diagnostics optimal. Ready for your command."

    @staticmethod
    def contains_wake_word(text: str) -> bool:
        """Checks if text contains the wake word 'jarvis'."""
        return bool(WAKE_WORD_REGEX.search(text))

    @staticmethod
    def strip_wake_word(text: str) -> str:
        """Removes the wake word prefix or suffix from the instruction."""
        s = re.sub(r"^(?:hey\s+|hai\s+|halo\s+|ok\s+)?(?:jarvis|jarvius|javis|jarviz)[,:\s]*", "", text, flags=re.IGNORECASE).strip()
        s = re.sub(r"[,:\s]*(?:hey\s+|hai\s+|halo\s+|ok\s+)?(?:jarvis|jarvius|javis|jarviz)$", "", s, flags=re.IGNORECASE).strip()
        return s

    @staticmethod
    def is_call_or_greeting(text: str) -> bool:
        """
        Determines if the user is just calling Jarvis or greeting him
        (e.g., 'Jarvis', 'Halo Jarvis', 'Hey Jarvis', 'Pagi Jarvis')
        without specifying a full OS task.
        """
        cleaned = VoiceService.strip_wake_word(text).strip().lower()
        cleaned = re.sub(r"[^\w\s]", "", cleaned).strip()
        greeting_words = {
            "", "halo", "hai", "hey", "hello", "hi", "pagi", "selamat pagi",
            "siang", "selamat siang", "sore", "selamat sore", "malam", "selamat malam",
            "yes", "ya", "sir", "bro", "jarvis", "jarvius", "javis", "ada",
            "selamat", "apa kabar"
        }
        return cleaned in greeting_words or len(cleaned) == 0

    @staticmethod
    def get_greeting_reply(text: str = "") -> str:
        """
        Returns polite human-like acknowledgment as requested:
        'Yes Sir, ada yang bisa saya bantu?' (Indonesian default)
        or English if user spoke English.
        """
        lower = text.lower()
        if any(w in lower for w in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return "Yes, Sir. How may I help you?"
        return "Yes Sir, ada yang bisa saya bantu?"

    def start_background_listening(self, callback: Callable[[str], None], status_callback: Optional[Callable[[str], None]] = None):
        """
        Starts background microphone listener with:
        1. 5-second silence detection.
        2. Wake-word ('Jarvis') activation and conversational follow-up window.
        """
        if not sr or not self.recognizer:
            print("[VoiceService] SpeechRecognition not available.")
            return

        def listen_worker():
            try:
                with sr.Microphone() as source:
                    print("[VoiceService] Calibrating microphone for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    print("[VoiceService] Continuous listening active. Waiting for wake word 'Jarvis' with 5s pause...")

                    while self._is_listening:
                        if status_callback:
                            status_callback("AWAITING_COMMAND" if self.is_awaiting_command() else "STANDBY")
                        try:
                            # Listen for phrase (blocks until 5s pause after speech ends)
                            audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                            if status_callback:
                                status_callback("PROCESSING_SPEECH")

                            # Transcribe
                            text = ""
                            try:
                                text = self.recognizer.recognize_google(audio, language="id-ID")
                            except sr.UnknownValueError:
                                try:
                                    text = self.recognizer.recognize_google(audio, language="en-US")
                                except Exception:
                                    text = ""
                            except Exception:
                                pass

                            if text and text.strip():
                                recognized = text.strip()
                                has_wake = self.contains_wake_word(recognized)
                                awaiting = self.is_awaiting_command()

                                if not has_wake and not awaiting:
                                    print(f"[VoiceService] Ambient speech ignored (no 'Jarvis' wake word): '{recognized}'")
                                    if status_callback:
                                        status_callback(f"IGNORED_NO_WAKE_WORD:{recognized}")
                                    continue

                                # If we were awaiting command and user didn't repeat 'Jarvis':
                                if awaiting and not has_wake:
                                    print(f"\n[VoiceService] Active conversation follow-up received: '{recognized}'")
                                    self.set_awaiting_command(False)
                                    if status_callback:
                                        status_callback(f"COMMAND_ACTIVE:{recognized}")
                                else:
                                    print(f"\n[VoiceService] Wake word 'Jarvis' detected! Utterance: '{recognized}'")
                                    if status_callback:
                                        status_callback(f"WAKE_WORD_ACTIVE:{recognized}")

                                callback(recognized)

                        except sr.WaitTimeoutError:
                            continue
                        except Exception as ex:
                            time.sleep(0.5)

            except Exception as e:
                print(f"[VoiceService] Background mic thread error: {e}")

        self._is_listening = True
        t = threading.Thread(target=listen_worker, daemon=True, name="JarvisVoiceListener")
        t.start()

    def stop_background_listening(self):
        self._is_listening = False
