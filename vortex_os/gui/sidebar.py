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
        self._indicators = {}
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
            ("◈",  "ai",       "ARIA AI Assistant  [Ctrl+A]"),  
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
     """
     Creates a dock button with a running indicator dot below it.
     The container holds both the button and the dot.
     """
     # Container for button + indicator dot
     container = QWidget()
     container.setFixedSize(self.WIDTH - 4, self.WIDTH)
     container.setStyleSheet("background: transparent;")

     c_layout = QVBoxLayout()
     c_layout.setContentsMargins(0, 0, 0, 0)
     c_layout.setSpacing(1)

     btn = QPushButton(icon)
     btn.setFixedSize(self.WIDTH - 4, self.WIDTH - 10)
     btn.setStyleSheet(DOCK_BUTTON)
     btn.setToolTip(tooltip)
     btn.setFont(QFont("monospace", 18))
     btn.clicked.connect(lambda checked, a=action: self._on_click(a))

    # Running indicator dot (hidden by default)
     dot = QLabel("●")
     dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
     dot.setFixedHeight(8)
     dot.setStyleSheet("color: transparent; font-size: 7px;")

     c_layout.addWidget(btn)
     c_layout.addWidget(dot)
     container.setLayout(c_layout)

     self._buttons[action]    = btn
     self._indicators[action] = dot

     return container

    def update_indicator(self, action, active):
     """
     Sows or hides the running dot under a dock button.

    Args:
        action : button action string (e.g. "terminal")
        active : True = show glowing dot, False = hide
    """
     dot = self._indicators.get(action)
     if dot is None:
        return

     if active:
        dot.setStyleSheet("color: #00ffff; font-size: 7px;")
     else:
        dot.setStyleSheet("color: transparent; font-size: 7px;")
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