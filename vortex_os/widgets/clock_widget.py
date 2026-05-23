# widgets/clock_widget.py
# VORTEX OS - Floating Clock Widget

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore    import Qt, QTimer, QRectF
from PyQt6.QtGui     import QFont, QColor, QPainter, QPen, QFontDatabase

import datetime

from widgets.base_widget import BaseWidget


class ClockWidget(BaseWidget):
    """
    Floating clock widget for VORTEX OS.

    Displays:
    - Large digital time (HH:MM:SS)
    - Date and day of week
    - Animated seconds arc (circular progress indicator)
    - UNIX timestamp

    Updates every second via QTimer.
    """

    DEFAULT_X      = 50
    DEFAULT_Y      = 50
    DEFAULT_WIDTH  = 320
    DEFAULT_HEIGHT = 280
    BORDER_COLOR   = "#00ffff"    # Cyan for clock

    def get_title(self):
        return "VORTEX CLOCK"

    def setup_ui(self):
        """Builds the clock layout."""
        # Main layout with padding
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(4)

        # ── Header label ──────────────────────────
        self.lbl_header = QLabel("◈ VORTEX CLOCK")
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header.setStyleSheet(
            "color: #00ffff; font-size: 11px; font-weight: bold; "
            "letter-spacing: 3px;"
        )

        # ── Time label (large) ────────────────────
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet(
            "color: #00ffff; font-size: 42px; font-weight: bold; "
            "font-family: monospace; letter-spacing: 4px;"
        )

        # ── Date label ────────────────────────────
        self.lbl_date = QLabel("MONDAY, 01 JAN 2026")
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_date.setStyleSheet(
            "color: #ffffff; font-size: 12px; letter-spacing: 2px;"
        )

        # ── Seconds arc canvas ────────────────────
        # This is a custom widget just for drawing the arc
        self.arc_canvas = _SecondsArc()
        self.arc_canvas.setFixedHeight(60)

        # ── UNIX timestamp ────────────────────────
        self.lbl_unix = QLabel("UNIX: 0000000000")
        self.lbl_unix.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_unix.setStyleSheet(
            "color: #444466; font-size: 10px; font-family: monospace;"
        )

        # ── Close hint ────────────────────────────
        lbl_hint = QLabel("ESC to close  ·  drag to move")
        lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_hint.setStyleSheet("color: #333355; font-size: 9px;")

        # Assemble
        layout.addWidget(self.lbl_header)
        layout.addSpacing(6)
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.lbl_date)
        layout.addWidget(self.arc_canvas)
        layout.addWidget(self.lbl_unix)
        layout.addWidget(lbl_hint)

        self.setLayout(layout)

        # ── Timer: fires every 1000ms (1 second) ─
        self.timer = QTimer(self)          # parent=self ties lifetime to widget
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time() 
    def _update_time(self):
        """Called every second to refresh all displayed values."""
        now = datetime.datetime.now()

        self.lbl_time.setText(now.strftime("%H:%M:%S"))
        self.lbl_date.setText(now.strftime("%A, %d %B %Y").upper())
        self.lbl_unix.setText(f"UNIX: {int(now.timestamp())}")

        # Tell the arc to redraw with the new seconds value
        self.arc_canvas.set_seconds(now.second)


class _SecondsArc(QWidget):
    """
    Custom widget that draws a circular arc representing the
    current seconds value (0–59) as a progress ring.

    Why a separate class?
    Because custom painting logic belongs in its own class.
    ClockWidget stays clean and readable.
    """

    def __init__(self):
        super().__init__()
        self._seconds = 0

    def set_seconds(self, seconds):
        """Updates seconds value and triggers a repaint."""
        self._seconds = seconds
        self.update()   # Schedules a paintEvent call

    def paintEvent(self, event):
        """Draws the seconds arc."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2
        radius = min(w, h) // 2 - 8

        # Background circle (dim)
        painter.setPen(QPen(QColor("#1a1a2e"), 4))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # Progress arc
        # Qt arcs: startAngle in 1/16 degrees, 0 = 3 o'clock
        # We want 12 o'clock start = 90 degrees = 1440 sixteenths
        # Negative span = clockwise direction
        span_degrees = (self._seconds / 60.0) * 360.0
        start = 90 * 16
        span  = -int(span_degrees * 16)

        arc_color = QColor("#00ffff")
        if self._seconds > 45:
            arc_color = QColor("#ff4444")    # Red when almost a minute
        elif self._seconds > 30:
            arc_color = QColor("#ffff00")    # Yellow at 30s

        painter.setPen(QPen(arc_color, 4))
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawArc(rect, start, span)

        # Center text: seconds number
        painter.setPen(QPen(QColor("#00ffff"), 1))
        font = QFont("monospace", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._seconds:02d}s"
        )