# core/app_manager.py
# VORTEX OS - Application Manager
# Owns the QApplication instance and manages widget launching
# safely from the main thread using Qt signals.

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import QObject, pyqtSignal, QTimer
import sys


class AppManager(QObject):
    """
    Singleton that owns QApplication and lives on the main thread.

    Why QObject?
    Only QObjects can use Qt signals and slots.
    Signals are the ONLY safe way to communicate between threads in Qt.

    How cross-thread widget launching works:
    1. Terminal thread calls request_widget("clock")
    2. That emits widget_requested signal
    3. Qt automatically queues the signal for the main thread
    4. Main thread's slot _launch_widget() runs and creates the widget
    5. Widget is safely created on the main thread — no segfault
    """

    # Signal emitted when terminal wants to open a widget.
    # str = widget name ("clock", "calendar", etc.)
    widget_requested = pyqtSignal(str)

    def __init__(self):
        # QApplication must exist before any QObject
        self.app = QApplication.instance() or QApplication(sys.argv)
        super().__init__()

        # Registry: name → widget class
        self._widget_registry = {}

        # Track open widgets so we don't duplicate
        self._open_widgets = {}

        # Connect signal to slot — Qt handles thread-safe queuing
        self.widget_requested.connect(self._launch_widget)

    def register_widget(self, name, widget_class):
        """Register a widget class under a name."""
        self._widget_registry[name] = widget_class

    def request_widget(self, name):
        """
        Called from ANY thread to request a widget open.
        Emitting a signal is thread-safe in Qt.
        The actual widget creation happens on the main thread.
        """
        self.widget_requested.emit(name)

    def _launch_widget(self, name):
        """
        Slot — always runs on main thread because it's connected
        to a signal emitted from another thread (Qt queues it).

        Creates the widget, shows it, and tracks it.
        """
        if name not in self._widget_registry:
            return

        # If already open, just bring to front
        if name in self._open_widgets and self._open_widgets[name].isVisible():
            self._open_widgets[name].raise_()
            self._open_widgets[name].activateWindow()
            return

        widget_class = self._widget_registry[name]
        try:
            widget = widget_class()
            widget.show()
            self._open_widgets[name] = widget
        except Exception as e:
            print(f"\n  [GUI ERROR] Failed to launch '{name}': {e}\n")

    def run(self):
        """
        Starts the Qt event loop on the main thread.
        This BLOCKS until the application quits.
        Everything else must run in threads or via signals.
        """
        return self.app.exec()

    def quit(self):
        """Safely quits the Qt application."""
        self.app.quit()


# Global singleton — imported by widget commands
_app_manager = None


def get_app_manager():
    """Returns the global AppManager instance."""
    return _app_manager


def set_app_manager(manager):
    """Called once by vortex_core.py during boot."""
    global _app_manager
    _app_manager = manager