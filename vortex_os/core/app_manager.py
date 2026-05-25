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
        widget_requested(str)  : open a named widget
        desktop_show_requested : show/raise the desktop window
    """

    widget_requested       = pyqtSignal(str)
    desktop_show_requested = pyqtSignal()      # ← NEW

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

        # Do NOT quit when last window closes.
        # The terminal thread owns the quit lifecycle.
        self.app.setQuitOnLastWindowClosed(False)

        super().__init__()

        self._widget_registry = {}
        self._open_widgets    = {}
        self._desktop         = None   # Set by launch_desktop()

        # Connect signals to slots — Qt handles thread-safe queuing
        self.widget_requested.connect(self._launch_widget)
        self.desktop_show_requested.connect(self._show_desktop)  # ← NEW

    def register_widget(self, name, widget_class):
        """Register a widget class under a name."""
        self._widget_registry[name] = widget_class

    def request_widget(self, name):
        """
        Safe to call from ANY thread.
        Emitting a signal is the only thread-safe way to
        trigger GUI work from a non-main thread.
        """
        self.widget_requested.emit(name)

    def request_show_desktop(self):
        """
        Safe to call from ANY thread.
        Asks the main thread to show and raise the desktop.
        """
        self.desktop_show_requested.emit()              # ← NEW

    def _launch_widget(self, name):
        """Slot — always runs on main thread."""
        if name not in self._widget_registry:
            return

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
        """
        Slot — always runs on main thread.
        Shows, raises, and activates the desktop window.
        """
        if self._desktop is None:
            print("\n  [!] Desktop not initialized yet.\n")
            return

        # Show if hidden
        if not self._desktop.isVisible():
            self._desktop.show()

        # Bring to front
        self._desktop.raise_()
        self._desktop.activateWindow()

    def launch_desktop(self):
        """
        Creates and shows the VortexDesktop window.
        Called once from the main thread after QApplication exists.
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


# ── Global singleton ──────────────────────────────────────

_app_manager = None


def get_app_manager():
    """Returns the global AppManager instance."""
    return _app_manager


def set_app_manager(manager):
    """Called once by vortex_core.py during boot."""
    global _app_manager
    _app_manager = manager