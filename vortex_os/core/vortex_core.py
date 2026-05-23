# core/vortex_core.py
# VORTEX OS - Core Initializer (Phase 4 fix)
# Qt runs on main thread. Terminal runs in QThread.

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtCore import QThread, pyqtSignal, QObject


class TerminalThread(QThread):
    """
    Runs the VORTEX terminal shell inside a Qt-managed thread.

    Why QThread instead of threading.Thread?
    QThread integrates with Qt's event system properly.
    It can safely emit signals to the main thread.
    threading.Thread has no knowledge of Qt's rules.

    The terminal runs here, completely independent of the GUI.
    When the user types 'exit', finished signal fires and
    the main thread's Qt app quits cleanly.
    """

    # Emitted when the shell exits normally
    shell_finished = pyqtSignal()

    def run(self):
        """
        QThread.run() is the thread's entry point.
        Everything here runs on the worker thread, not main thread.
        """
        try:
            from terminal.shell import VortexShell
            shell = VortexShell()
            shell.run()
        except Exception as e:
            print(f"\n[FATAL] Shell crashed: {e}")
        finally:
            # Always signal completion so Qt can quit
            self.shell_finished.emit()


class VortexCore(QObject):
    """
    Main coordinator. Lives on the main thread.
    Owns AppManager (Qt) and TerminalThread.
    """

    def __init__(self):
        # AppManager must be created FIRST — it creates QApplication
        from core.app_manager import AppManager, set_app_manager
        self.app_manager = AppManager()
        set_app_manager(self.app_manager)

        # Now QApplication exists, safe to call super().__init__()
        super().__init__()

        # Register all widgets with the manager
        self._register_widgets()

        # Create terminal thread (does not start yet)
        self.terminal_thread = TerminalThread()

        # When shell exits → quit Qt → program ends
        self.terminal_thread.shell_finished.connect(
            self.app_manager.quit
        )

    def _register_widgets(self):
        """Tells AppManager about all available widgets."""
        from widgets.clock_widget    import ClockWidget
        from widgets.calendar_widget import CalendarWidget

        self.app_manager.register_widget("clock",    ClockWidget)
        self.app_manager.register_widget("calendar", CalendarWidget)

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

    def boot(self):
        """
        Boot sequence:
        1. Play sound
        2. Start terminal thread
        3. Hand control to Qt event loop (blocks here until exit)
        """
        self._play_startup_sound()

        # Start the terminal in its thread
        self.terminal_thread.start()

        # Run Qt event loop on main thread — blocks until app.quit()
        return self.app_manager.run()


def launch():
    core = VortexCore()
    sys.exit(core.boot())