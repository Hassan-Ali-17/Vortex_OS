# core/vortex_core.py
# VORTEX OS - Core Initializer
# Phase 10: boot screen plays before desktop appears.

import os
import sys
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer


class TerminalThread(QThread):
    """
    Runs the VORTEX terminal shell in a Qt-managed thread.
    Emits shell_finished when the user types exit.
    """

    shell_finished = pyqtSignal()

    def run(self):
        try:
            from terminal.shell import VortexShell
            shell = VortexShell()
            shell.run()
        except Exception as e:
            print(f"\n[FATAL] Shell crashed: {e}")
        finally:
            self.shell_finished.emit()


class VortexCore(QObject):
    """
    Main coordinator. Lives on the main thread.
    Boot sequence:
      1. Show boot screen (fullscreen animation)
      2. Boot screen emits boot_complete
      3. Start terminal thread
      4. Show desktop
    """

    def __init__(self):
        # AppManager creates QApplication — must be first
        from core.app_manager import AppManager, set_app_manager
        self.app_manager = AppManager()
        set_app_manager(self.app_manager)

        super().__init__()

        self._register_widgets()
        self._config = self._load_config()

        # Create terminal thread (not started yet)
        self.terminal_thread = TerminalThread()
        self.terminal_thread.shell_finished.connect(
            self.app_manager.quit
        )

    def _load_config(self):
        """Loads settings.json for boot config."""
        try:
            with open("config/settings.json", "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _register_widgets(self):
        """Registers all floating widgets with AppManager."""
        from widgets.clock_widget    import ClockWidget
        from widgets.calendar_widget import CalendarWidget
        from widgets.monitor_widget  import MonitorWidget

        self.app_manager.register_widget("clock",    ClockWidget)
        self.app_manager.register_widget("calendar", CalendarWidget)
        self.app_manager.register_widget("monitor",  MonitorWidget)

    def _play_startup_sound(self):
        """Optional startup sound via PulseAudio."""
        sound_paths = [
            "/usr/share/sounds/ubuntu/stereo/system-ready.ogg",
            "/usr/share/sounds/freedesktop/stereo/service-login.oga",
            "/usr/share/sounds/freedesktop/stereo/bell.oga",
        ]
        for path in sound_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen(
                        ["paplay", path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return
                except FileNotFoundError:
                    return

    def _after_boot(self):
        """
        Called when boot screen finishes (or is skipped).
        Starts the terminal thread and launches the desktop.
        """
        # Start terminal in background thread
        self.terminal_thread.start()

        # Launch desktop on main thread after short delay
        QTimer.singleShot(100, self.app_manager.launch_desktop)

    def boot(self):
        """
        Main boot sequence.

        If boot animation enabled:
            show boot screen → wait for boot_complete → show desktop

        If boot animation disabled:
            skip straight to terminal + desktop
        """
        self._play_startup_sound()

        boot_cfg = self._config.get("boot", {})
        enabled  = boot_cfg.get("enabled", True)

        if enabled:
            # Show boot screen
            from gui.boot_screen import BootScreen
            self._boot_screen = BootScreen(config=self._config)

            # When animation finishes → proceed
            self._boot_screen.boot_complete.connect(self._after_boot)

        else:
            # Skip boot animation — go straight to desktop
            self._after_boot()

        # Hand control to Qt event loop
        return self.app_manager.run()


def launch():
    """Entry point called by main.py."""
    core = VortexCore()
    sys.exit(core.boot())