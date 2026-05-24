# gui/topbar.py
# VORTEX OS - Top Bar Panel
# Shows OS name, live clock, CPU and RAM usage.

import datetime
import os

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore    import QTimer, Qt

from gui.styles import (
    TOPBAR, TOPBAR_LABEL_OS,
    TOPBAR_LABEL_CLOCK, TOPBAR_LABEL_STATS
)


class TopBar(QWidget):
    """
    Horizontal bar across the top of the desktop.

    Layout:  [OS Name]  ----spacer----  [Clock]  [Stats]

    Updates:
    - Clock  : every 1 second
    - Stats  : every 3 seconds (reading /proc is cheap but not free)
    """

    HEIGHT = 36

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(TOPBAR)
        self._build_ui()
        self._start_timers()

    def _build_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Left: OS name ──────────────────────────
        self.lbl_os = QLabel("◈ VORTEX OS")
        self.lbl_os.setStyleSheet(TOPBAR_LABEL_OS)

        # ── Spacer: pushes clock to center-right ───
        # QLabel with stretch acts as a flexible spacer
        spacer = QLabel("")
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy(),
            spacer.sizePolicy().verticalPolicy()
        )

        # ── Center: live clock ─────────────────────
        self.lbl_clock = QLabel("00:00:00")
        self.lbl_clock.setStyleSheet(TOPBAR_LABEL_CLOCK)
        self.lbl_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_clock.setMinimumWidth(120)

        # ── Right: system stats ────────────────────
        self.lbl_stats = QLabel("CPU: --%  RAM: --MB")
        self.lbl_stats.setStyleSheet(TOPBAR_LABEL_STATS)
        self.lbl_stats.setAlignment(Qt.AlignmentFlag.AlignRight
                                   | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.lbl_os)
        layout.addStretch(1)
        layout.addWidget(self.lbl_clock)
        layout.addStretch(1)
        layout.addWidget(self.lbl_stats)

        self.setLayout(layout)

    def _start_timers(self):
        # Clock timer — fires every second
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Stats timer — fires every 3 seconds
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(3000)
        self._update_stats()

    def _update_clock(self):
        """Updates the clock label with current time."""
        now = datetime.datetime.now()
        self.lbl_clock.setText(now.strftime("%H:%M:%S"))

    def _update_stats(self):
        """
        Reads CPU load and RAM from /proc.
        Both files are virtual — reading them is near-instant.
        """
        # ── RAM ──────────────────────────────────
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            total_kb = int(lines[0].split()[1])
            avail_kb = int(lines[2].split()[1])
            used_mb  = (total_kb - avail_kb) // 1024
            total_mb = total_kb // 1024
            ram_str  = f"RAM {used_mb}M/{total_mb}M"
        except Exception:
            ram_str = "RAM --"

        # ── CPU load average ─────────────────────
        try:
            load = os.getloadavg()
            cpu_str = f"LOAD {load[0]:.1f}"
        except Exception:
            cpu_str = "LOAD --"

        self.lbl_stats.setText(f"{cpu_str}  {ram_str}")