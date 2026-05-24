# gui/styles.py
# VORTEX OS - Centralized Qt Stylesheet Definitions
# All QSS (Qt Style Sheets) strings live here.
# QSS is similar to CSS but for Qt widgets.

# ── Palette ────────────────────────────────────────────────
# These are raw color constants used to build QSS strings.
# We define them here rather than reading from ThemeEngine
# because QSS is applied at widget-creation time, not
# dynamically — full live theme switching in GUI comes Phase 8.

BG_DARK       = "#07070f"     # Main background — near black
BG_PANEL      = "#0d0d1a"     # Panels, bars
BG_WIDGET     = "#0a0a14"     # Widget backgrounds
BG_HOVER      = "#1a1a2e"     # Hover state
BG_SELECTED   = "#16213e"     # Selected state

CYAN          = "#00ffff"
CYAN_DIM      = "#006666"
CYAN_DARK     = "#003333"
MAGENTA       = "#cc00ff"
MAGENTA_DIM   = "#660088"
GREEN         = "#00ff88"
GREEN_DIM     = "#006633"
RED           = "#ff3355"
YELLOW        = "#ffcc00"
WHITE         = "#e0e0ff"
GREY          = "#444466"
GREY_DARK     = "#222233"
BORDER        = "#1a1a3e"


# ── Top Bar ────────────────────────────────────────────────

TOPBAR = f"""
    QWidget#TopBar {{
        background-color: {BG_PANEL};
        border-bottom: 1px solid {CYAN_DIM};
    }}
"""

TOPBAR_LABEL_OS = f"""
    QLabel {{
        color: {CYAN};
        font-size: 13px;
        font-weight: bold;
        font-family: monospace;
        letter-spacing: 3px;
        padding-left: 12px;
    }}
"""

TOPBAR_LABEL_CLOCK = f"""
    QLabel {{
        color: {GREEN};
        font-size: 13px;
        font-weight: bold;
        font-family: monospace;
        letter-spacing: 2px;
    }}
"""

TOPBAR_LABEL_STATS = f"""
    QLabel {{
        color: {GREY};
        font-size: 11px;
        font-family: monospace;
        padding-right: 12px;
    }}
"""


# ── Sidebar Dock ───────────────────────────────────────────

SIDEBAR = f"""
    QWidget#Sidebar {{
        background-color: {BG_PANEL};
        border-right: 1px solid {CYAN_DARK};
    }}
"""

DOCK_BUTTON = f"""
    QPushButton {{
        background-color: transparent;
        color: {GREY};
        border: none;
        border-radius: 8px;
        font-size: 22px;
        padding: 8px;
        margin: 2px 6px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        color: {CYAN};
        border: 1px solid {CYAN_DIM};
    }}
    QPushButton:pressed {{
        background-color: {CYAN_DARK};
        color: {CYAN};
    }}
"""

DOCK_BUTTON_ACTIVE = f"""
    QPushButton {{
        background-color: {CYAN_DARK};
        color: {CYAN};
        border: 1px solid {CYAN_DIM};
        border-radius: 8px;
        font-size: 22px;
        padding: 8px;
        margin: 2px 6px;
    }}
"""

DOCK_SEPARATOR = f"""
    QFrame {{
        color: {CYAN_DARK};
        background-color: {CYAN_DARK};
    }}
"""


# ── Desktop Canvas ─────────────────────────────────────────

DESKTOP_CANVAS = f"""
    QWidget#DesktopCanvas {{
        background-color: {BG_DARK};
    }}
"""

DESKTOP_BRAND_LABEL = f"""
    QLabel {{
        color: {CYAN_DARK};
        font-size: 64px;
        font-weight: bold;
        font-family: monospace;
        letter-spacing: 8px;
    }}
"""

DESKTOP_SUB_LABEL = f"""
    QLabel {{
        color: {MAGENTA_DIM};
        font-size: 13px;
        font-family: monospace;
        letter-spacing: 5px;
    }}
"""


# ── Embedded Terminal ──────────────────────────────────────

TERMINAL_CONTAINER = f"""
    QWidget#TerminalContainer {{
        background-color: {BG_WIDGET};
        border: 1px solid {CYAN_DIM};
        border-radius: 4px;
    }}
"""

TERMINAL_TITLEBAR = f"""
    QWidget#TerminalTitlebar {{
        background-color: {BG_PANEL};
        border-bottom: 1px solid {CYAN_DARK};
        border-radius: 0px;
    }}
"""

TERMINAL_TITLE_LABEL = f"""
    QLabel {{
        color: {CYAN};
        font-size: 10px;
        font-weight: bold;
        font-family: monospace;
        letter-spacing: 2px;
        padding-left: 8px;
    }}
"""

TERMINAL_OUTPUT = f"""
    QTextEdit {{
        background-color: {BG_DARK};
        color: {WHITE};
        font-family: monospace;
        font-size: 12px;
        border: none;
        padding: 8px;
        selection-background-color: {CYAN_DARK};
    }}
"""

TERMINAL_INPUT = f"""
    QLineEdit {{
        background-color: {BG_PANEL};
        color: {CYAN};
        font-family: monospace;
        font-size: 12px;
        border: none;
        border-top: 1px solid {CYAN_DARK};
        padding: 6px 8px;
    }}
"""

TERMINAL_CLOSE_BTN = f"""
    QPushButton {{
        background: transparent;
        color: {GREY};
        border: none;
        font-size: 13px;
        padding: 2px 8px;
    }}
    QPushButton:hover {{
        color: {RED};
    }}
"""


# ── Bottom Taskbar ─────────────────────────────────────────

TASKBAR = f"""
    QWidget#Taskbar {{
        background-color: {BG_PANEL};
        border-top: 1px solid {CYAN_DARK};
    }}
"""

TASKBAR_BUTTON = f"""
    QPushButton {{
        background-color: {BG_WIDGET};
        color: {GREY};
        border: 1px solid {BORDER};
        border-radius: 3px;
        font-family: monospace;
        font-size: 10px;
        padding: 3px 10px;
        margin: 4px 2px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        color: {WHITE};
        border-color: {CYAN_DIM};
    }}
"""

TASKBAR_LABEL = f"""
    QLabel {{
        color: {GREY_DARK};
        font-size: 10px;
        font-family: monospace;
        padding: 0px 8px;
    }}
"""


# ── Notification / Tooltip ─────────────────────────────────

NOTIFICATION = f"""
    QWidget#Notification {{
        background-color: {BG_PANEL};
        border: 1px solid {CYAN_DIM};
        border-radius: 4px;
    }}
    QLabel {{
        color: {WHITE};
        font-size: 11px;
        font-family: monospace;
        padding: 4px 10px;
    }}
"""