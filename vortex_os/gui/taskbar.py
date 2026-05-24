# gui/taskbar.py
# VORTEX OS - Bottom Taskbar
# Shows open apps and quick-action buttons.

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal

from gui.styles import TASKBAR, TASKBAR_BUTTON, TASKBAR_LABEL


class BottomTaskbar(QWidget):
    """
    Horizontal bar along the bottom of the desktop.

    Left side  : open app indicators (updated by desktop)
    Right side : quick-action buttons (terminal, widgets)

    Emits 'action_requested' signal when buttons are clicked.
    """

    action_requested = pyqtSignal(str)
    HEIGHT = 32

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Taskbar")
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(TASKBAR)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)

        # ── Left: open app tags ────────────────────
        self.lbl_apps = QLabel("◈ VORTEX OS  v0.1.0  GENESIS")
        self.lbl_apps.setStyleSheet(TASKBAR_LABEL)

        # ── Spacer ─────────────────────────────────
        layout.addWidget(self.lbl_apps)
        layout.addStretch(1)

        # ── Right: quick actions ───────────────────
        quick_actions = [
            ("▶ TERMINAL", "terminal"),
            ("◉ CLOCK",    "clock"),
            ("◈ CALENDAR", "calendar"),
        ]

        for label, action in quick_actions:
            btn = QPushButton(label)
            btn.setStyleSheet(TASKBAR_BUTTON)
            btn.clicked.connect(
                lambda checked, a=action: self.action_requested.emit(a)
            )
            layout.addWidget(btn)

        self.setLayout(layout)

    def set_open_apps(self, app_names):
        """
        Updates the left side with currently open app names.
        Called by the desktop whenever a widget opens/closes.
        """
        if app_names:
            tags = "  ·  ".join(f"[{n}]" for n in app_names)
            self.lbl_apps.setText(f"◈  {tags}")
        else:
            self.lbl_apps.setText("◈ VORTEX OS  v0.1.0  GENESIS")