# widgets/monitor_widget.py
# VORTEX OS - System Monitor Widget
# Live CPU, RAM, and disk graphs using QPainter sparklines.

import os
import time
import shutil
import collections

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore    import QTimer, Qt
from PyQt6.QtGui     import (
    QPainter, QColor, QPen,
    QLinearGradient, QFont
)

from widgets.base_widget import BaseWidget


# How many data points to keep in the sparkline history
HISTORY_LENGTH = 60


class SparklineGraph(QWidget):
    """
    A single sparkline graph widget.
    Draws a filled area chart from a deque of float values (0.0–100.0).

    Why deque?
    deque(maxlen=N) automatically drops the oldest item when you
    append to a full deque. Perfect for a rolling history window.
    """

    def __init__(self, label, color, parent=None):
        super().__init__(parent)
        self.label      = label
        self.color      = QColor(color)
        self.data       = collections.deque(
                            [0.0] * HISTORY_LENGTH,
                            maxlen=HISTORY_LENGTH
                          )
        self.current    = 0.0
        self.setFixedHeight(56)
        self.setMinimumWidth(200)

    def push(self, value):
        """Add a new data point (0.0–100.0) and trigger redraw."""
        self.current = max(0.0, min(100.0, value))
        self.data.append(self.current)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self.data)

        # ── Background ────────────────────────────
        painter.fillRect(0, 0, w, h, QColor("#07070f"))

        # ── Sparkline area fill ───────────────────
        if n < 2:
            return

        step = w / (n - 1)

        # Build polygon points for filled area
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF

        points = []
        for i, val in enumerate(self.data):
            x = i * step
            y = h - (val / 100.0) * (h - 12) - 4
            points.append(QPointF(x, y))

        # Close the polygon at the bottom
        points.append(QPointF((n - 1) * step, h))
        points.append(QPointF(0, h))

        # Gradient fill under the line
        grad = QLinearGradient(0, 0, 0, h)
        fill_color = QColor(self.color)
        fill_color.setAlpha(60)
        grad.setColorAt(0.0, fill_color)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        from PyQt6.QtGui import QPolygonF as _PF
        poly = _PF([p for p in points])
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(poly)

        # Line on top
        pen = QPen(self.color, 1.5)
        painter.setPen(pen)
        for i in range(len(points) - 3):
            painter.drawLine(points[i], points[i + 1])

        # ── Label + value ─────────────────────────
        painter.setPen(QPen(QColor("#444466")))
        painter.setFont(QFont("monospace", 8))
        painter.drawText(4, 12, self.label)

        value_color = QColor(self.color)
        painter.setPen(QPen(value_color))
        painter.setFont(QFont("monospace", 9, QFont.Weight.Bold))
        painter.drawText(
            0, 0, w - 4, 16,
            Qt.AlignmentFlag.AlignRight,
            f"{self.current:.0f}%"
        )


class MonitorWidget(BaseWidget):
    """
    Floating system monitor with live sparkline graphs.

    Monitors:
    - CPU load average (1 min) scaled to percentage
    - RAM usage percentage
    - Swap usage percentage
    - Disk usage of root partition
    """

    DEFAULT_X      = 100
    DEFAULT_Y      = 100
    DEFAULT_WIDTH  = 300
    DEFAULT_HEIGHT = 360
    BORDER_COLOR   = "#00ff88"

    def get_title(self):
        return "VORTEX MONITOR"

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── Header ─────────────────────────────────
        lbl_header = QLabel("◈ SYSTEM MONITOR")
        lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_header.setStyleSheet(
            "color: #00ff88; font-size: 11px; font-weight: bold; "
            "letter-spacing: 3px;"
        )

        # ── Sparkline graphs ───────────────────────
        self.graph_cpu  = SparklineGraph("CPU LOAD",  "#00ffff")
        self.graph_ram  = SparklineGraph("RAM",       "#00ff88")
        self.graph_swap = SparklineGraph("SWAP",      "#cc00ff")
        self.graph_disk = SparklineGraph("DISK  /",   "#ffcc00")

        # ── Text summary row ───────────────────────
        self.lbl_summary = QLabel("Collecting data...")
        self.lbl_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_summary.setStyleSheet(
            "color: #444466; font-size: 9px; font-family: monospace;"
        )

        # ── Uptime ─────────────────────────────────
        self.lbl_uptime = QLabel("")
        self.lbl_uptime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_uptime.setStyleSheet(
            "color: #333355; font-size: 9px; font-family: monospace;"
        )

        # ── Hint ───────────────────────────────────
        lbl_hint = QLabel("ESC to close  ·  drag to move")
        lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_hint.setStyleSheet("color: #222233; font-size: 9px;")

        layout.addWidget(lbl_header)
        layout.addWidget(self.graph_cpu)
        layout.addWidget(self.graph_ram)
        layout.addWidget(self.graph_swap)
        layout.addWidget(self.graph_disk)
        layout.addWidget(self.lbl_summary)
        layout.addWidget(self.lbl_uptime)
        layout.addWidget(lbl_hint)

        self.setLayout(layout)

        # Timer: update every 1 second
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._collect)
        self._timer.start(1000)
        self._collect()

    def _collect(self):
        """
        Reads system metrics from /proc files and updates graphs.
        All reads are from virtual files — fast and lightweight.
        """
        # ── CPU load ──────────────────────────────
        try:
            load1 = os.getloadavg()[0]
            # Load average is absolute (e.g. 1.5 on a 4-core = 37.5%)
            # We cap at 100% for display
            cpu_count = os.cpu_count() or 1
            cpu_pct   = min(100.0, (load1 / cpu_count) * 100.0)
            self.graph_cpu.push(cpu_pct)
        except Exception:
            self.graph_cpu.push(0.0)

        # ── RAM ───────────────────────────────────
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            total_kb = int(lines[0].split()[1])
            avail_kb = int(lines[2].split()[1])
            used_kb  = total_kb - avail_kb
            ram_pct  = (used_kb / total_kb) * 100.0

            # Swap (lines 14 and 15 in /proc/meminfo)
            swap_total = int(lines[14].split()[1])
            swap_free  = int(lines[15].split()[1])
            if swap_total > 0:
                swap_pct = ((swap_total - swap_free) / swap_total) * 100.0
            else:
                swap_pct = 0.0

            self.graph_ram.push(ram_pct)
            self.graph_swap.push(swap_pct)

            # Summary text
            used_mb  = used_kb  // 1024
            total_mb = total_kb // 1024
            self.lbl_summary.setText(
                f"RAM  {used_mb}M / {total_mb}M  |  "
                f"CPU  {cpu_pct:.0f}%"
            )

        except Exception:
            self.graph_ram.push(0.0)
            self.graph_swap.push(0.0)

        # ── Disk ──────────────────────────────────
        try:
            total, used, free = shutil.disk_usage("/")
            disk_pct = (used / total) * 100.0
            self.graph_disk.push(disk_pct)
        except Exception:
            self.graph_disk.push(0.0)

        # ── Uptime ────────────────────────────────
        try:
            with open('/proc/uptime', 'r') as f:
                secs = float(f.read().split()[0])
            h = int(secs // 3600)
            m = int((secs % 3600) // 60)
            self.lbl_uptime.setText(f"uptime  {h}h {m}m")
        except Exception:
            pass