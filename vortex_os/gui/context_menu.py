# gui/context_menu.py
# VORTEX OS - Right-click desktop context menu

from PyQt6.QtWidgets import QMenu, QWidgetAction, QLabel
from PyQt6.QtGui     import QAction, QFont
from PyQt6.QtCore    import Qt


def _make_header(text):
    """Creates a non-clickable styled header item for the menu."""
    label = QLabel(f"  {text}")
    label.setStyleSheet(
        "color: #444466; font-size: 9px; font-family: monospace; "
        "letter-spacing: 2px; padding: 4px 8px 2px 8px;"
    )
    action = QWidgetAction(None)
    action.setDefaultWidget(label)
    return action


MENU_STYLE = """
    QMenu {
        background-color: #0d0d1a;
        border: 1px solid #00ffff;
        border-radius: 4px;
        padding: 4px 0px;
        font-family: monospace;
        font-size: 12px;
        color: #e0e0ff;
    }
    QMenu::item {
        padding: 6px 28px 6px 16px;
        background-color: transparent;
    }
    QMenu::item:selected {
        background-color: #1a1a2e;
        color: #00ffff;
    }
    QMenu::item:disabled {
        color: #333355;
    }
    QMenu::separator {
        height: 1px;
        background-color: #1a1a2e;
        margin: 4px 8px;
    }
"""


def build_context_menu(parent, callbacks):
    """
    Builds the right-click desktop context menu.

    Args:
        parent    : parent widget (desktop canvas)
        callbacks : dict mapping action keys to callables
                    {
                        "terminal":   fn,
                        "clock":      fn,
                        "calendar":   fn,
                        "monitor":    fn,
                        "fullscreen": fn,
                        "theme_list": [("cyberpunk", fn), ...],
                    }

    Returns:
        QMenu instance ready to exec_()
    """
    menu = QMenu(parent)
    menu.setStyleSheet(MENU_STYLE)

    # ── Apps section ──────────────────────────────────
    menu.addAction(_make_header("LAUNCH"))

    def _add(icon, label, key):
        action = QAction(f"{icon}  {label}", parent)
        cb = callbacks.get(key)
        if cb:
            action.triggered.connect(cb)
        else:
            action.setEnabled(False)
        menu.addAction(action)

    _add("▶", "Terminal",        "terminal")
    _add("◉", "Clock Widget",    "clock")
    _add("◈", "Calendar Widget", "calendar")
    _add("⚡", "System Monitor",  "monitor")

    menu.addSeparator()

    # ── Theme submenu ──────────────────────────────────
    menu.addAction(_make_header("THEME"))

    theme_menu = QMenu("  ◐  Change Theme", parent)
    theme_menu.setStyleSheet(MENU_STYLE)

    theme_list = callbacks.get("theme_list", [])
    for theme_name, theme_cb in theme_list:
        act = QAction(f"  {theme_name.upper()}", parent)
        act.triggered.connect(theme_cb)
        theme_menu.addAction(act)

    menu.addMenu(theme_menu)
    menu.addSeparator()

    # ── System section ─────────────────────────────────
    menu.addAction(_make_header("SYSTEM"))
    _add("⛶", "Toggle Fullscreen", "fullscreen")
    _add("✕", "Hide Desktop",      "hide_desktop")

    return menu