# core/app_manager.py
# VORTEX OS - Application Manager
# Owns QApplication. All GUI operations requested via signals.

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import QObject, pyqtSignal
import sys


class AppManager(QObject):
    """
    Singleton that owns QApplication and lives on the main thread.

    All cross-thread GUI requests go through signals.
    Never call Qt widget methods directly from another thread.

    Signals:
        widget_requested(str)   : open a named floating widget
        desktop_show_requested  : show/raise the desktop window
        app_launch_requested(str): launch an app by id
    """

    widget_requested       = pyqtSignal(str)
    desktop_show_requested = pyqtSignal()
    app_launch_requested   = pyqtSignal(str)

    def __init__(self):
        # ── Step 1: QApplication must exist first ──────────────
        # QApplication must be created before ANY QObject,
        # including ourselves. super().__init__() creates a QObject
        # which requires QApplication to already exist.
        self.app = QApplication.instance() or QApplication(sys.argv)

        # Do NOT quit when last window closes.
        # The terminal thread owns the quit lifecycle.
        self.app.setQuitOnLastWindowClosed(False)

        # ── Step 2: Now safe to call QObject __init__ ──────────
        # Only AFTER QApplication exists can we call super().__init__()
        # Without this, any signal/slot operation raises RuntimeError.
        super().__init__()

        # ── Step 3: Internal state ─────────────────────────────
        self._widget_registry = {}
        self._open_widgets    = {}
        self._desktop         = None

        # ── Step 4: Connect signals to slots ───────────────────
        # Connections can only happen after super().__init__() above.
        # Qt requires the object to be fully initialised first.
        self.widget_requested.connect(self._launch_widget)
        self.desktop_show_requested.connect(self._show_desktop)
        self.app_launch_requested.connect(self._launch_app)

    # ─────────────────────────────────────────────
    #  PUBLIC API — safe to call from any thread
    # ─────────────────────────────────────────────

    def register_widget(self, name, widget_class):
        """Register a floating widget class under a name."""
        self._widget_registry[name] = widget_class

    def request_widget(self, name):
        """
        Thread-safe widget open request.
        Emitting a signal is the only safe cross-thread Qt operation.
        """
        self.widget_requested.emit(name)

    def request_show_desktop(self):
        """Thread-safe desktop show request."""
        self.desktop_show_requested.emit()

    def launch_desktop(self):
        """
        Creates and shows the VortexDesktop window.
        Must be called from the main thread after QApplication exists.
        """
        from gui.desktop import VortexDesktop
        self._desktop = VortexDesktop()
        self._desktop.show()

    def run(self):
        """Starts the Qt event loop. Blocks until app.quit()."""
        return self.app.exec()

    def quit(self):
        """Safely quits the Qt application."""
        self.app.quit()

    def _do_reboot_animation(self):
     """
    Runs on the main thread (called via QTimer.singleShot).
    Shows boot screen, hides desktop, restores desktop when done.
    """
     import json

    # Load config for boot settings
     try:
        with open("config/settings.json", "r") as f:
            cfg = json.load(f)
     except Exception:
        cfg = {}

     from gui.boot_screen import BootScreen

    # Hide desktop while boot plays
     if self._desktop and self._desktop.isVisible():
        self._desktop.hide()

    # Create and show boot screen
     self._reboot_screen = BootScreen(config=cfg)

    # When boot finishes restore the desktop
     def _restore():
        if self._desktop:
            self._desktop.show()
            self._desktop.raise_()
            self._desktop.activateWindow()
        # Clean up reference
        self._reboot_screen = None

     self._reboot_screen.boot_complete.connect(_restore)   

    # ─────────────────────────────────────────────
    #  SLOTS — always run on main thread
    #  Qt routes cross-thread signals here safely.
    # ─────────────────────────────────────────────

    def _launch_widget(self, name):
        """Opens a named floating widget."""
        if name not in self._widget_registry:
            return

        # If already open and visible, just raise it
        if name in self._open_widgets:
            w = self._open_widgets[name]
            if w.isVisible():
                w.raise_()
                w.activateWindow()
                return

        widget_class = self._widget_registry[name]
        try:
            widget = widget_class()
            widget.show()
            self._open_widgets[name] = widget
        except Exception as e:
            print(f"\n  [GUI ERROR] Failed to launch '{name}': {e}\n")

    def _show_desktop(self):
        """Shows and raises the desktop window."""
        if self._desktop is None:
            print("\n  [!] Desktop not initialized yet.\n")
            return

        if not self._desktop.isVisible():
            self._desktop.show()

        self._desktop.raise_()
        self._desktop.activateWindow()

    def _launch_app(self, app_id):
     """
    Launches a VORTEX app by id via the AppRegistry.
    Runs on main thread — safe to create Qt widgets here.
    Also notifies the desktop taskbar.
    """
     from apps.registry import get_registry
     registry        = get_registry()
     success, result = registry.launch(app_id)

     if success:
        # Tell the desktop to show this app in the taskbar
        if self._desktop:
            manifest = registry.get(app_id)
            if manifest:
                name = manifest.get("name", app_id).upper()
                self._desktop._add_open_app(name)

                # When the app closes, remove it from taskbar
                # result is the app instance when success=True
                result.app_closed.connect(
                    lambda aid, n=name:
                        self._desktop._remove_open_app(n)
                )
     else:
        print(f"\n  [APP ERROR] {result}\n")

# ── Global singleton ──────────────────────────────────────

_app_manager = None


def get_app_manager():
    """Returns the global AppManager instance."""
    return _app_manager


def set_app_manager(manager):
    """Called once by vortex_core.py during boot."""
    global _app_manager
    _app_manager = manager