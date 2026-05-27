# apps/base_app.py
# VORTEX OS - Base App Class
# All VORTEX apps inherit from this.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore    import pyqtSignal


class BaseApp(QWidget):
    """
    Base class for all VORTEX OS applications.

    Every app is a QWidget subclass. This means:
    - Apps are GUI widgets by default
    - They can be shown, hidden, moved, resized
    - They get the cyberpunk styling system

    Required override:
        setup_ui(self) : build the app's interface

    Optional overrides:
        on_launch(self)  : called when app is first shown
        on_close(self)   : called when app is closed
        get_title(self)  : returns window title string

    Signals:
        app_closed : emitted when the app window closes
    """

    app_closed = pyqtSignal(str)   # str = app id

    def __init__(self, manifest, parent=None):
        super().__init__(parent)

        self.manifest   = manifest
        self.app_id     = manifest.get("id",      "unknown")
        self.app_name   = manifest.get("name",    "App")
        self.app_version= manifest.get("version", "1.0.0")

        # Common window flags for all apps
        from PyQt6.QtCore import Qt
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose, False
        )

        self.setWindowTitle(self.get_title())
        self._apply_base_style()
        self.setup_ui()

    def _apply_base_style(self):
        """Applies the base cyberpunk stylesheet to all apps."""
        self.setStyleSheet("""
            QWidget {
                background-color: #07070f;
                color: #e0e0ff;
                font-family: monospace;
            }
            QLabel {
                color: #e0e0ff;
            }
            QPushButton {
                background-color: #0d0d1a;
                color: #00ffff;
                border: 1px solid #003333;
                padding: 6px 14px;
                font-family: monospace;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1a1a2e;
                border-color: #00ffff;
            }
            QPushButton:pressed {
                background-color: #003333;
            }
            QLineEdit, QTextEdit {
                background-color: #0a0a14;
                color: #00ffff;
                border: 1px solid #003333;
                padding: 4px;
                font-family: monospace;
            }
            QScrollBar:vertical {
                background: #07070f;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #1a1a2e;
                min-height: 20px;
            }
        """)

    def get_title(self):
        """Override to set a custom window title."""
        return f"◈ {self.app_name}  v{self.app_version}"

    def setup_ui(self):
        """Override this to build the app's UI."""
        pass

    def on_launch(self):
        """Called when the app is shown. Override for init logic."""
        pass

    def on_close(self):
        """Called when the app is closed. Override for cleanup."""
        pass

    def closeEvent(self, event):
        """Emits app_closed signal before hiding."""
        self.on_close()
        self.app_closed.emit(self.app_id)
        self.hide()
        event.ignore()   # Don't destroy — just hide