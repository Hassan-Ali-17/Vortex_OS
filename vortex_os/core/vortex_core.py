# core/vortex_core.py
# VORTEX OS - Core Initializer

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from terminal.shell import VortexShell


class VortexCore:
    """
    Core engine of VORTEX OS.
    Handles boot sequence including optional startup sound.
    """

    def __init__(self):
        self.shell = VortexShell()

    def _play_startup_sound(self):
        """
        Plays a startup sound using Ubuntu's built-in system sounds.
        Uses subprocess so the shell doesn't freeze waiting for audio.
        Fails silently — audio is optional, never critical.
        """
        # Ubuntu stores system sounds here
        sound_paths = [
            "/usr/share/sounds/ubuntu/stereo/system-ready.ogg",
            "/usr/share/sounds/freedesktop/stereo/service-login.oga",
            "/usr/share/sounds/freedesktop/stereo/bell.oga",
        ]

        for path in sound_paths:
            if os.path.exists(path):
                try:
                    # Run paplay in background so shell starts immediately
                    # stdout/stderr are suppressed — we don't want audio
                    # errors cluttering the terminal
                    subprocess.Popen(
                        ["paplay", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return   # Stop after first found sound
                except FileNotFoundError:
                    # paplay not installed — skip silently
                    return

    def boot(self):
        """
        Boot sequence: play sound, then launch terminal.
        """
        self._play_startup_sound()
        self.shell.run()


def launch():
    core = VortexCore()
    core.boot()