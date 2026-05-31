# commands/voice_commands.py
# VORTEX OS - Voice command terminal interface

from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


@with_timestamp
def cmd_voice(args, config):
    """
    Command: voice [on | off | once | speak <text> | status]

    voice on      → start continuous voice command listening
    voice off     → stop listening
    voice once    → listen for one phrase
    voice speak <text> → speak text aloud
    voice status  → show voice engine status
    voice test    → speak a test phrase
    """
    from core.voice_engine import get_voice_engine
    engine = get_voice_engine()

    if not args or args[0].lower() == "status":
        _voice_status(engine)
        return

    sub = args[0].lower()

    if sub == "once":
        _voice_once(engine, config)

    elif sub == "on":
        _voice_continuous_on(engine, config)

    elif sub == "off":
        _voice_continuous_off(engine)

    elif sub == "speak":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: "
                  f"voice speak <text>{COLORS.RESET}\n")
            return
        text = " ".join(args[1:])
        _voice_speak(engine, text)

    elif sub == "test":
        _voice_speak(
            engine,
            "ARIA voice system online. VORTEX OS is ready."
        )

    else:
        print(f"{COLORS.ERROR}  [!] Unknown subcommand: "
              f"'{sub}'{COLORS.RESET}")
        print(f"  {COLORS.DIM}Options: on | off | once | "
              f"speak | test | status{COLORS.RESET}\n")


def _voice_status(engine):
    """Shows current voice engine status."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VOICE ENGINE STATUS"
          f"{COLORS.RESET}\n")

    tts_ok  = engine._tts_engine is not None
    mic_ok  = _check_microphone()

    print(f"  {COLORS.PRIMARY}TTS ENGINE  : "
          f"{COLORS.SUCCESS if tts_ok else COLORS.ERROR}"
          f"{'OK' if tts_ok else 'NOT AVAILABLE'}{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}MICROPHONE  : "
          f"{COLORS.SUCCESS if mic_ok else COLORS.ERROR}"
          f"{'DETECTED' if mic_ok else 'NOT DETECTED'}{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}LISTENING   : "
          f"{COLORS.TEXT}{engine._listening}{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}LANGUAGE    : "
          f"{COLORS.TEXT}"
          f"{engine._config.get('language', 'en-US')}{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}SPEAK RESP  : "
          f"{COLORS.TEXT}"
          f"{engine._config.get('speak_responses', True)}"
          f"{COLORS.RESET}\n")


def _check_microphone():
    """Returns True if a microphone is available."""
    try:
        import speech_recognition as sr
        sr.Microphone()
        return True
    except Exception:
        return False


def _voice_once(engine, config):
    """Listens for one phrase and processes it."""
    print(f"\n{COLORS.ACCENT}  ◈ Listening... speak now."
          f"{COLORS.RESET}")
    print(f"  {COLORS.DIM}Speak a VORTEX command or question."
          f"{COLORS.RESET}\n")

    # Connect signal to handler
    def _on_speech(text):
        print(f"\n{COLORS.SUCCESS}  ◈ Heard: \"{text}\""
              f"{COLORS.RESET}")
        _process_voice_input(text, engine, config)

    def _on_error(msg):
        print(f"\n{COLORS.ERROR}  [!] {msg}{COLORS.RESET}\n")

    engine.speech_recognized.connect(_on_speech)
    engine.error_occurred.connect(_on_error)
    engine.listen_once()


def _voice_continuous_on(engine, config):
    """Starts continuous voice command listening."""
    print(f"\n{COLORS.SUCCESS}  ◈ Voice command mode ACTIVE."
          f"{COLORS.RESET}")
    print(f"  {COLORS.DIM}Speak commands or questions."
          f"{COLORS.RESET}")
    print(f"  {COLORS.DIM}Type 'voice off' to stop."
          f"{COLORS.RESET}\n")

    def _on_speech(text):
        print(f"\n{COLORS.ACCENT}  ◈ Voice: \"{text}\""
              f"{COLORS.RESET}")
        _process_voice_input(text, engine, config)

    engine.start_continuous_listening(_on_speech)


def _voice_continuous_off(engine):
    """Stops continuous listening."""
    engine.stop_continuous_listening()
    print(f"\n{COLORS.WARNING}  ◈ Voice command mode OFF."
          f"{COLORS.RESET}\n")


def _voice_speak(engine, text):
    """Speaks text aloud."""
    print(f"\n{COLORS.ACCENT}  ◈ Speaking: \"{text}\""
          f"{COLORS.RESET}\n")
    engine.speak(text)


def _process_voice_input(text, engine, config):
    """
    Decides what to do with recognized speech.

    Priority order:
    1. Check if it is a VORTEX command → execute it
    2. Otherwise → send to ARIA AI

    VORTEX command detection:
    We check if the spoken text starts with a known
    command word from the router registry.
    """
    lower = text.lower().strip()

    # Get registered commands from config router
    router = config.get("_router")
    if router:
        known_commands = list(router._registry.keys())

        for cmd in known_commands:
            if lower.startswith(cmd) or lower == cmd:
                print(f"  {COLORS.PRIMARY}→ Executing command: "
                      f"{COLORS.TEXT}{text}{COLORS.RESET}\n")
                engine.speak(f"Running {cmd}")

                # Execute via router
                from terminal.parser import CommandParser
                parser = CommandParser()
                parsed = parser.parse(text)
                if parsed:
                    router.execute(parsed, config)
                return

    # Not a command — send to ARIA
    print(f"  {COLORS.PRIMARY}→ Sending to ARIA..."
          f"{COLORS.RESET}\n")
    _send_to_aria(text, engine, config)


def _send_to_aria(text, engine, config):
    """
    Sends voice input to the ARIA AI and speaks the response.
    """
    try:
        from core.voice_engine import get_voice_engine
        from openai import OpenAI
        import json

        # Load AI config
        try:
            with open("config/ai_config.json", "r") as f:
                ai_cfg = json.load(f)
        except Exception:
            ai_cfg = {}

        api_key = ai_cfg.get("api_key", "").strip()
        if not api_key:
            import os
            api_key = os.environ.get("GROQ_API_KEY", "").strip()

        if not api_key:
            print(f"{COLORS.ERROR}  [!] No API key for ARIA."
                  f"{COLORS.RESET}\n")
            return

        client = OpenAI(
            api_key  = api_key,
            base_url = "https://api.groq.com/openai/v1"
        )

        response = client.chat.completions.create(
            model    = ai_cfg.get("model", "llama-3.3-70b-versatile"),
            messages = [
                {
                    "role":    "system",
                    "content": ai_cfg.get("system_prompt", "")
                },
                {
                    "role":    "user",
                    "content": text
                }
            ],
            max_tokens = 200   # Keep voice responses short
        )

        reply = response.choices[0].message.content.strip()
        print(f"\n{COLORS.ACCENT}  ARIA: {COLORS.TEXT}{reply}"
              f"{COLORS.RESET}\n")

        # Speak the response
        ve = get_voice_engine()
        ve.speak(reply)

    except Exception as e:
        print(f"{COLORS.ERROR}  [!] ARIA voice error: {e}"
              f"{COLORS.RESET}\n")