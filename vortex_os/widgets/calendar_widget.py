# widgets/calendar_widget.py
# VORTEX OS - Floating Calendar Widget

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont, QColor

import datetime
import calendar

from widgets.base_widget import BaseWidget


class CalendarWidget(BaseWidget):
    """
    Floating calendar widget for VORTEX OS.

    Displays:
    - Current month as a grid (Mon–Sun columns)
    - Today highlighted in cyan
    - Previous/next month navigation buttons
    - Selected date shown at the bottom
    - Week numbers on the left
    """

    DEFAULT_X      = 400
    DEFAULT_Y      = 50
    DEFAULT_WIDTH  = 390
    DEFAULT_HEIGHT = 380
    BORDER_COLOR   = "#cc00ff"    # Magenta for calendar

    def get_title(self):
        return "VORTEX CALENDAR"

    def setup_ui(self):
        """Builds the calendar layout."""
        self._today        = datetime.date.today()
        self._view_year    = self._today.year
        self._view_month   = self._today.month
        self._selected_day = None

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        # ── Header ─────────────────────────────────
        header_label = QLabel("◈ VORTEX CALENDAR")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet(
            "color: #cc00ff; font-size: 11px; font-weight: bold; "
            "letter-spacing: 3px;"
        )

        # ── Month navigation row ────────────────────
        nav_layout = QHBoxLayout()

        self.btn_prev = QPushButton("◀")
        self.btn_next = QPushButton("▶")

        for btn in (self.btn_prev, self.btn_next):
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(
                "QPushButton { background: #1a0a2e; color: #cc00ff; "
                "border: 1px solid #cc00ff; font-weight: bold; }"
                "QPushButton:hover { background: #cc00ff; color: #000000; }"
            )

        self.lbl_month = QLabel()
        self.lbl_month.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_month.setStyleSheet(
            "color: #ffffff; font-size: 13px; font-weight: bold; "
            "letter-spacing: 2px;"
        )

        self.btn_prev.clicked.connect(self._prev_month)
        self.btn_next.clicked.connect(self._next_month)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_month)
        nav_layout.addWidget(self.btn_next)

        # ── Calendar grid ───────────────────────────
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        self.grid_widget.setLayout(self.grid_layout)

        # ── Selected date display ───────────────────
        self.lbl_selected = QLabel("Click a day to select")
        self.lbl_selected.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_selected.setStyleSheet(
            "color: #888899; font-size: 10px; font-style: italic;"
        )

        # ── Hint ────────────────────────────────────
        lbl_hint = QLabel("ESC to close  ·  drag to move")
        lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_hint.setStyleSheet("color: #333355; font-size: 9px;")

        # Assemble
        layout.addWidget(header_label)
        layout.addLayout(nav_layout)
        layout.addWidget(self.grid_widget)
        layout.addWidget(self.lbl_selected)
        layout.addWidget(lbl_hint)

        self.setLayout(layout)

        # Draw the initial month
        self._render_calendar()

    def _render_calendar(self):
     """
    Clears and redraws the calendar grid.

    Grid layout (Phase 4 homework update):
    Col 0      : Week number header / week numbers per row
    Col 1–7    : Day name headers / day buttons (Mon–Sun)
     """
    # Clear existing grid
     while self.grid_layout.count():
        item = self.grid_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    # Update month/year label
     month_date = datetime.date(self._view_year, self._view_month, 1)
     self.lbl_month.setText(month_date.strftime("%B %Y").upper())

    # ── Row 0: Column headers ──────────────────────

    # Week number column header
     wk_header = QLabel("WK")
     wk_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
     wk_header.setStyleSheet(
        "color: #cc00ff; font-size: 9px; font-weight: bold; "
        "letter-spacing: 1px;"
     )
     self.grid_layout.addWidget(wk_header, 0, 0)

    # Day name headers (Mon–Sun) in columns 1–7
     day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
     for col, name in enumerate(day_names, start=1):
        lbl = QLabel(name)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Weekends (SAT=col 6, SUN=col 7) get red tint
        color = "#ff4444" if col >= 6 else "#888899"
        lbl.setStyleSheet(
            f"color: {color}; font-size: 9px; font-weight: bold; "
            f"letter-spacing: 1px;"
        )
        self.grid_layout.addWidget(lbl, 0, col)

    # ── Rows 1+: Weeks ─────────────────────────────

     cal = calendar.monthcalendar(self._view_year, self._view_month)
 
     for row, week in enumerate(cal, start=1):

        # Calculate ISO week number for this row.
        # Find the first non-zero day in the week to get the date.
        # Every week has at least one valid day.
        week_day_num = next(d for d in week if d != 0)
        week_date    = datetime.date(self._view_year, self._view_month, week_day_num)
        iso_week     = week_date.isocalendar().week

        # Week number label in column 0
        wk_label = QLabel(str(iso_week))
        wk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wk_label.setFixedSize(28, 28)
        wk_label.setStyleSheet(
            "color: #662288; font-size: 9px; font-weight: bold;"
        )
        self.grid_layout.addWidget(wk_label, row, 0)

        # Day buttons in columns 1–7
        for col, day in enumerate(week, start=1):
            if day == 0:
                # Empty — outside this month
                spacer = QLabel("")
                spacer.setFixedSize(36, 28)
                self.grid_layout.addWidget(spacer, row, col)
            else:
                btn = self._make_day_button(day, col)
                self.grid_layout.addWidget(btn, row, col)

    def _make_day_button(self, day, col):
     """col is now 1-based (1=Mon ... 7=Sun). Weekend = col 6 or 7."""
     is_today = (
        day == self._today.day and
        self._view_month == self._today.month and
        self._view_year  == self._today.year
     )
     is_selected = (day == self._selected_day)
     is_weekend  = col >= 6    # col 6=SAT, col 7=SUN

     btn = QPushButton(str(day))
     btn.setFixedSize(36, 28)

     if is_today:
        style = (
            "QPushButton { background: #00ffff; color: #000000; "
            "font-weight: bold; border: none; }"
            "QPushButton:hover { background: #00cccc; }"
        )
     elif is_selected:
        style = (
            "QPushButton { background: #cc00ff; color: #ffffff; "
            "font-weight: bold; border: none; }"
            "QPushButton:hover { background: #aa00dd; }"
        )
     elif is_weekend:
        style = (
            "QPushButton { background: transparent; color: #cc4444; "
            "border: none; }"
            "QPushButton:hover { background: #2a0a0a; }"
        )
     else:
        style = (
            "QPushButton { background: transparent; color: #aaaacc; "
            "border: none; }"
            "QPushButton:hover { background: #1a1a2e; }"
        )

     btn.setStyleSheet(style)
     btn.clicked.connect(lambda checked, d=day: self._select_day(d))
     return btn

    def _select_day(self, day):
        """Handles a day button click."""
        self._selected_day = day
        selected_date = datetime.date(self._view_year, self._view_month, day)
        formatted = selected_date.strftime("%A, %d %B %Y").upper()
        self.lbl_selected.setText(f"◈ {formatted}")
        self.lbl_selected.setStyleSheet(
            "color: #cc00ff; font-size: 10px; font-weight: bold;"
        )
        # Redraw to show selected highlight
        self._render_calendar()

    def _prev_month(self):
        """Navigate to previous month."""
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._selected_day = None
        self._render_calendar()

    def _next_month(self):
        """Navigate to next month."""
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._selected_day = None
        self._render_calendar()