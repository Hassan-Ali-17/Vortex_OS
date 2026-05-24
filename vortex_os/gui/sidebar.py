# gui/sidebar.py
# VORTEX OS - Left Sidebar Dock
# Contains icon buttons for launching apps and widgets.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QLabel, QFrame, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from gui.styles import SIDEBAR, DOCK_BUTTON, DOCK_SEPARATOR


class SidebarDock(QWidget):
    """
    Vertical icon dock on the left side of the desktop.

    Each button emits 'app_launched' signal with an action string.
    The desktop connects to this signal and handles the action.

    Why signals instead of direct calls?
    Loose coupling. The sidebar doesn't need to know anything
    about the desktop, terminal, or widgets. It just says
    "user clicked terminal" — the desktop decides what to do.
    """

    # Signal: emitted when a dock button is clicked
    # str = action identifier ("terminal", "clock", "calendar", etc.)
    app_launched = pyqtSignal(str)

    WIDTH = 56

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.WIDTH)
        self.setStyleSheet(SIDEBAR)
        self._active_action = None
        self._buttons = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Primary dock items ─────────────────────
        primary_items = [
            ("⬡",  "desktop",  "Desktop"),
            ("▶",  "terminal", "Terminal  [Ctrl+T]"),
            ("◉",  "clock",    "Clock Widget"),
            ("◈",  "calendar", "Calendar Widget"),
            ("⚡",  "scan",     "System Scanner"),
        ]

        for icon, action, tooltip in primary_items:
            btn = self._make_button(icon, action, tooltip)
            layout.addWidget(btn)

        # ── Separator ──────────────────────────────
        layout.addWidget(self._make_separator())
        layout.addStretch(1)

        # ── Bottom items ───────────────────────────
        bottom_items = [
            ("◐",  "theme",    "Theme Switcher"),
            ("⚙",  "settings", "Settings (Coming Soon)"),
        ]

        for icon, action, tooltip in bottom_items:
            btn = self._make_button(icon, action, tooltip)
            layout.addWidget(btn)

        self.setLayout(layout)

    def _make_button(self, icon, action, tooltip):
        """Creates a styled dock button."""
        btn = QPushButton(icon)
        btn.setFixedSize(self.WIDTH - 4, self.WIDTH - 4)
        btn.setStyleSheet(DOCK_BUTTON)
        btn.setToolTip(tooltip)
        btn.setFont(QFont("monospace", 18))

        # Capture action in lambda default arg (Python closure fix)
        btn.clicked.connect(lambda checked, a=action: self._on_click(a))

        self._buttons[action] = btn
        return btn

    def _make_separator(self):
        """Thin horizontal line between button groups."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(DOCK_SEPARATOR)
        return line

    def _on_click(self, action):
        """Handles dock button click — emits signal."""
        self.app_launched.emit(action)

    def set_active(self, action):
        """Highlights the button for the active app."""
        from gui.styles import DOCK_BUTTON_ACTIVE
        for name, btn in self._buttons.items():
            if name == action:
                btn.setStyleSheet(DOCK_BUTTON_ACTIVE)
            else:
                btn.setStyleSheet(DOCK_BUTTON)
        self._active_action = action