# gui/boot_screen.py
# VORTEX OS - Boot Animation Screen
#
# A fullscreen cinematic startup sequence.
# Everything drawn with QPainter — zero external assets.
#
# Boot stages (state machine):
#   0 - BIOS    : hardware detection table
#   1 - LOGO    : ASCII art letter-by-letter wipe
#   2 - INIT    : scrolling initialization messages
#   3 - LOADING : progress bar fills to 100%
#   4 - FLASH   : white flash transition
#   5 - DONE    : signal emitted, desktop takes over

import os
import math
import shutil
import platform
import datetime

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore    import Qt, QTimer, pyqtSignal
from PyQt6.QtGui     import (
    QPainter, QColor, QFont,
    QFontMetrics, QLinearGradient
)


# ── Stage constants ───────────────────────────────────────
STAGE_BIOS    = 0
STAGE_LOGO    = 1
STAGE_INIT    = 2
STAGE_LOADING = 3
STAGE_FLASH   = 4
STAGE_DONE    = 5

# ── ASCII logo — each character is one "column" ──────────
VORTEX_LOGO = [
    "██╗   ██╗",
    "██║   ██║",
    "██║   ██║",
    "╚██╗ ██╔╝",
    " ╚████╔╝ ",
    "  ╚═══╝  ",
]

VORTEX_LOGO_FULL = [
    "██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗",
    "██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝",
    "██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ ",
    "╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ ",
    " ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗",
    "  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝",
]


def _collect_hardware():
    """
    Reads real hardware info from /proc and platform module.
    Returns a list of (label, value, ok) tuples for the BIOS screen.
    """
    items = []

    # OS
    items.append((
        "SYSTEM",
        f"{platform.system()} {platform.release()}",
        True
    ))

    # CPU
    cpu = platform.processor() or platform.machine()
    items.append(("CPU", cpu[:40] if cpu else "Unknown", bool(cpu)))

    # RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total_mb = int(lines[0].split()[1]) // 1024
        avail_mb = int(lines[2].split()[1]) // 1024
        items.append((
            "RAM",
            f"{avail_mb} MB free / {total_mb} MB total",
            True
        ))
    except Exception:
        items.append(("RAM", "Unknown", False))

    # Disk
    try:
        total, used, free = shutil.disk_usage("/")
        total_gb = total // (1024 ** 3)
        free_gb  = free  // (1024 ** 3)
        items.append((
            "DISK",
            f"{free_gb} GB free / {total_gb} GB total",
            True
        ))
    except Exception:
        items.append(("DISK", "Unknown", False))

    # Python
    items.append((
        "RUNTIME",
        f"Python {platform.python_version()}",
        True
    ))

    # Display
    try:
        screen = QApplication.primaryScreen()
        geo    = screen.geometry()
        items.append((
            "DISPLAY",
            f"{geo.width()}x{geo.height()}",
            True
        ))
    except Exception:
        items.append(("DISPLAY", "Unknown", False))

    # Hostname
    items.append((
        "HOST",
        platform.node() or "localhost",
        True
    ))

    return items


def _build_init_messages():
    """
    Builds the list of fake-but-realistic init messages.
    Timestamps increment realistically.
    """
    base  = 0.001
    step  = 0.031
    msgs  = [
        "VORTEX kernel initializing",
        "Loading core modules",
        "Mounting virtual filesystem",
        "Starting theme engine",
        "Loading app registry",
        "Initializing command parser",
        "Starting terminal daemon",
        "Loading vx:// path resolver",
        "Mounting vx://core",
        "Mounting vx://vault",
        "Mounting vx://config",
        "Starting system monitor",
        "Initializing PyQt6 compositor",
        "Loading cyberpunk theme",
        "Starting desktop environment",
        "All systems nominal",
    ]

    result = []
    t      = base
    for msg in msgs:
        result.append((round(t, 3), msg))
        t += step + (hash(msg) % 10) * 0.005

    return result


class BootScreen(QWidget):
    """
    Full-screen boot animation widget.

    Signals:
        boot_complete : emitted when animation finishes.
                        VortexCore connects this to show the desktop.

    The screen manages itself through stages using QTimers.
    Each stage runs, then advances automatically.
    VortexCore just calls show() and waits for boot_complete.
    """

    boot_complete = pyqtSignal()

    def __init__(self, config=None, parent=None):
        super().__init__(parent)

        # Read boot config
        self._cfg = (config or {}).get("boot", {})

        # Full screen, no window chrome
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()

        # ── Animation state ───────────────────────
        self._stage        = STAGE_BIOS
        self._tick         = 0       # General animation tick
        self._bios_line    = 0       # How many BIOS lines shown
        self._logo_col     = 0       # How many logo columns revealed
        self._init_line    = 0       # How many init messages shown
        self._load_pct     = 0.0     # Loading bar 0.0–100.0
        self._flash_alpha  = 0       # Flash overlay alpha 0–255

        # ── Collected data ────────────────────────
        self._hw_items    = _collect_hardware()
        self._init_msgs   = _build_init_messages()

        # ── Scanline animation offset ─────────────
        self._scan_y      = 0.0

        # ── Main animation timer: 33ms ≈ 30fps ────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_animation)
        self._timer.start(33)

        # ── Stage advance timers ──────────────────
        # Each stage schedules the next one after its duration
        bios_duration = 100 * len(self._hw_items) + 600
        QTimer.singleShot(bios_duration,         self._start_logo)
        QTimer.singleShot(bios_duration + 1800,  self._start_init)
        QTimer.singleShot(bios_duration + 3400,  self._start_loading)
        QTimer.singleShot(bios_duration + 5200,  self._start_flash)
        QTimer.singleShot(bios_duration + 6000,  self._finish)

    # ─────────────────────────────────────────────
    #  STAGE TRANSITIONS
    # ─────────────────────────────────────────────

    def _start_logo(self):
        self._stage    = STAGE_LOGO
        self._logo_col = 0

        # Reveal one character column every 40ms
        self._logo_timer = QTimer(self)
        self._logo_timer.timeout.connect(self._advance_logo)
        self._logo_timer.start(28)

    def _advance_logo(self):
        """Reveals the logo one column of characters at a time."""
        max_cols = len(VORTEX_LOGO_FULL[0])
        if self._logo_col < max_cols:
            self._logo_col += 2   # Advance 2 chars per tick for speed
            self.update()
        else:
            self._logo_timer.stop()

    def _start_init(self):
        self._stage     = STAGE_INIT
        self._init_line = 0

        # Reveal one init message every 120ms
        self._init_timer = QTimer(self)
        self._init_timer.timeout.connect(self._advance_init)
        self._init_timer.start(110)

    def _advance_init(self):
        """Reveals init messages one line at a time."""
        if self._init_line < len(self._init_msgs):
            self._init_line += 1
            self.update()
        else:
            self._init_timer.stop()

    def _start_loading(self):
        self._stage    = STAGE_LOADING
        self._load_pct = 0.0

        # Fill loading bar smoothly
        self._load_timer = QTimer(self)
        self._load_timer.timeout.connect(self._advance_loading)
        self._load_timer.start(18)

    def _advance_loading(self):
        """Increments the loading bar."""
        if self._load_pct < 100.0:
            # Non-linear fill — fast at start, slows near 100%
            remaining     = 100.0 - self._load_pct
            increment     = max(0.4, remaining * 0.06)
            self._load_pct = min(100.0, self._load_pct + increment)
            self.update()
        else:
            self._load_timer.stop()

    def _start_flash(self):
        """White flash transition before desktop appears."""
        self._stage       = STAGE_FLASH
        self._flash_alpha = 0

        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._advance_flash)
        self._flash_timer.start(16)

    def _advance_flash(self):
        """Increases flash brightness then fades."""
        self._flash_alpha += 18
        if self._flash_alpha >= 255:
            self._flash_alpha = 255
            self._flash_timer.stop()
        self.update()

    def _finish(self):
        """Boot complete — emit signal and hide."""
        self._stage = STAGE_DONE
        self._timer.stop()
        self.hide()
        self.boot_complete.emit()

    # ─────────────────────────────────────────────
    #  ANIMATION TICK
    # ─────────────────────────────────────────────

    def _tick_animation(self):
        """Advances global tick counter and scanline."""
        self._tick   += 1
        self._scan_y  = (self._scan_y + 0.008) % 1.0

        # BIOS stage: reveal one line per ~100ms (every 3 ticks at 33ms)
        if self._stage == STAGE_BIOS:
            if self._tick % 3 == 0:
                if self._bios_line < len(self._hw_items):
                    self._bios_line += 1

        self.update()

    # ─────────────────────────────────────────────
    #  PAINTING
    # ─────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Black background always
        painter.fillRect(0, 0, w, h, QColor(0, 0, 0))

        # Draw current stage content
        if self._stage == STAGE_BIOS:
            self._draw_bios(painter, w, h)

        elif self._stage == STAGE_LOGO:
            self._draw_bios(painter, w, h)   # Keep BIOS visible
            self._draw_logo(painter, w, h)

        elif self._stage == STAGE_INIT:
            self._draw_logo(painter, w, h)
            self._draw_init(painter, w, h)

        elif self._stage == STAGE_LOADING:
            self._draw_logo(painter, w, h)
            self._draw_init(painter, w, h)
            self._draw_loading(painter, w, h)

        elif self._stage == STAGE_FLASH:
            self._draw_logo(painter, w, h)
            self._draw_loading(painter, w, h)
            self._draw_flash(painter, w, h)

        # Scanline overlay on all stages
        self._draw_scanlines(painter, w, h)

    def _draw_bios(self, painter, w, h):
        """
        Draws the BIOS-style hardware detection table.
        Lines appear one by one as _bios_line increments.
        """
        font = QFont("monospace", 13)
        painter.setFont(font)
        fm   = QFontMetrics(font)
        lh   = fm.height() + 6

        # Top-left corner position
        start_x = 60
        start_y  = 60

        # VORTEX BIOS header
        painter.setPen(QColor("#00ffff"))
        title_font = QFont("monospace", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(start_x, start_y, "VORTEX BIOS  v1.0.0")

        painter.setFont(font)
        painter.setPen(QColor("#333355"))
        painter.drawText(
            start_x, start_y + lh,
            "─" * 52
        )

        # Hardware lines — revealed one at a time
        for i in range(min(self._bios_line, len(self._hw_items))):
            label, value, ok = self._hw_items[i]

            y = start_y + lh * (i + 2) + 8

            # Label in dim cyan
            painter.setPen(QColor("#006666"))
            painter.drawText(start_x, y, f"{label:<12}")

            # Value in white
            painter.setPen(QColor("#aaaacc"))
            painter.drawText(start_x + fm.horizontalAdvance("X" * 13), y, value)

            # OK / FAIL badge
            if ok:
                painter.setPen(QColor("#00ff88"))
                painter.drawText(start_x + fm.horizontalAdvance("X" * 52), y, "[ OK ]")
            else:
                painter.setPen(QColor("#ff3355"))
                painter.drawText(start_x + fm.horizontalAdvance("X" * 52), y, "[FAIL]")

        # Blinking cursor after last line
        if (self._bios_line < len(self._hw_items) and
                self._tick % 20 < 10):
            y = start_y + lh * (self._bios_line + 2) + 8
            painter.setPen(QColor("#00ffff"))
            painter.drawText(start_x, y, "█")

    def _draw_logo(self, painter, w, h):
        """
        Draws the VORTEX ASCII logo centered on screen.
        Characters are revealed left-to-right via _logo_col.
        """
        font = QFont("monospace", 14, QFont.Weight.Bold)
        painter.setFont(font)
        fm   = QFontMetrics(font)

        logo_w  = fm.horizontalAdvance(VORTEX_LOGO_FULL[0])
        logo_h  = len(VORTEX_LOGO_FULL) * (fm.height() + 4)

        start_x = (w - logo_w) // 2
        start_y = (h // 2) - (logo_h // 2) - 40

        for row_idx, line in enumerate(VORTEX_LOGO_FULL):
            y = start_y + row_idx * (fm.height() + 4)

            # Only draw up to _logo_col characters
            visible = line[:self._logo_col]

            # Glow effect: draw slightly offset in darker color first
            painter.setPen(QColor(0, 80, 80))
            painter.drawText(start_x + 1, y + 1, visible)

            # Main color: bright cyan
            painter.setPen(QColor("#00ffff"))
            painter.drawText(start_x, y, visible)

        # Tagline under logo — only after logo is fully revealed
        if self._logo_col >= len(VORTEX_LOGO_FULL[0]):
            tag_font = QFont("monospace", 11)
            painter.setFont(tag_font)
            painter.setPen(QColor("#cc00ff"))
            tagline  = "INITIALIZE  ·  DOMINATE  ·  EVOLVE"
            tag_w    = QFontMetrics(tag_font).horizontalAdvance(tagline)
            painter.drawText(
                (w - tag_w) // 2,
                start_y + logo_h + 16,
                tagline
            )

    def _draw_init(self, painter, w, h):
        """
        Draws scrolling init messages in the lower half.
        Each line has a timestamp and status.
        """
        font = QFont("monospace", 11)
        painter.setFont(font)
        fm   = QFontMetrics(font)
        lh   = fm.height() + 3

        # Show last N messages that fit
        max_visible = 10
        start_x     = 80
        base_y      = h - (max_visible * lh) - 60

        visible_msgs = self._init_msgs[:self._init_line]
        display_msgs = visible_msgs[-max_visible:]

        for i, (ts, msg) in enumerate(display_msgs):
            y        = base_y + i * lh
            is_last  = (i == len(display_msgs) - 1)

            # Timestamp
            painter.setPen(QColor("#333355"))
            painter.drawText(start_x, y, f"[ {ts:>7.3f} ]")

            # Message text
            color = QColor("#00ff88") if is_last else QColor("#446644")
            painter.setPen(color)
            painter.drawText(start_x + 110, y, msg)

            # OK badge on all but last (last is "in progress")
            if not is_last:
                painter.setPen(QColor("#006633"))
                painter.drawText(start_x + 110 + 340, y, "✓")

        # Blinking cursor on last active line
        if (self._init_line > 0 and
                self._init_line <= len(self._init_msgs) and
                self._tick % 16 < 8):
            y = base_y + (len(display_msgs) - 1) * lh
            painter.setPen(QColor("#00ff88"))
            painter.drawText(
                start_x + 110 + 340, y, "█"
            )

    def _draw_loading(self, painter, w, h):
        """
        Draws the loading progress bar at the bottom of the screen.
        """
        bar_w    = int(w * 0.6)
        bar_h    = 8
        bar_x    = (w - bar_w) // 2
        bar_y    = h - 80

        pct      = self._load_pct / 100.0
        filled_w = int(bar_w * pct)

        # Label above bar
        font = QFont("monospace", 11, QFont.Weight.Bold)
        painter.setFont(font)
        fm   = QFontMetrics(font)

        label     = "BOOTING VORTEX OS"
        label_w   = fm.horizontalAdvance(label)
        painter.setPen(QColor("#00ffff"))
        painter.drawText((w - label_w) // 2, bar_y - 20, label)

        # Bar background
        painter.fillRect(bar_x, bar_y, bar_w, bar_h, QColor("#0a0a14"))

        # Bar fill — gradient from cyan to magenta
        if filled_w > 0:
            grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
            grad.setColorAt(0.0, QColor("#00ffff"))
            grad.setColorAt(0.6, QColor("#0088ff"))
            grad.setColorAt(1.0, QColor("#cc00ff"))
            painter.fillRect(bar_x, bar_y, filled_w, bar_h, grad)

        # Bar border
        from PyQt6.QtGui import QPen
        painter.setPen(QPen(QColor("#003333"), 1))
        painter.drawRect(bar_x, bar_y, bar_w, bar_h)

        # Percentage text
        pct_font = QFont("monospace", 10)
        painter.setFont(pct_font)
        pct_str  = f"{int(self._load_pct)}%"
        pct_w    = QFontMetrics(pct_font).horizontalAdvance(pct_str)
        painter.setPen(QColor("#888899"))
        painter.drawText((w - pct_w) // 2, bar_y + bar_h + 20, pct_str)

    def _draw_flash(self, painter, w, h):
        """Draws the white flash overlay for stage transition."""
        flash_color = QColor(255, 255, 255, min(self._flash_alpha, 255))
        painter.fillRect(0, 0, w, h, flash_color)

    def _draw_scanlines(self, painter, w, h):
        """
        Draws subtle CRT-style horizontal scanlines over everything.
        This gives the screen a retro monitor feel.
        """
        scanline_color = QColor(0, 0, 0, 28)
        spacing        = 3

        for y in range(0, h, spacing):
            painter.fillRect(0, y, w, 1, scanline_color)

        # Moving bright scanline
        scan_y = int(self._scan_y * h)
        bright = QColor(0, 255, 255, 10)
        painter.fillRect(0, scan_y, w, 2, bright)