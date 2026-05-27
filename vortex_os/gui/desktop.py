# gui/desktop.py
# VORTEX OS - Main Desktop Environment Window
# Clean Phase 8 version — no leftover Phase 5 code.

import os
import math

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QApplication,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui  import (
    QPainter, QColor, QBrush,
    QLinearGradient, QKeySequence, QShortcut
)

from gui.topbar       import TopBar
from gui.sidebar      import SidebarDock
from gui.taskbar      import BottomTaskbar
from gui.tab_terminal import TabTerminal
from gui.context_menu import build_context_menu
from gui.styles       import (
    DESKTOP_CANVAS,
    DESKTOP_BRAND_LABEL,
    DESKTOP_SUB_LABEL
)


# ─────────────────────────────────────────────────────────
#  DESKTOP CANVAS
#  Pure background widget.
#  Draws animated dots, scan line, vignette, branding text.
#  Owns NO child widgets — terminal lives in VortexDesktop.
# ─────────────────────────────────────────────────────────

class DesktopCanvas(QWidget):
    """
    Animated cyberpunk background for the VORTEX desktop.
    Does only one thing: draw the background.
    All interactive widgets are owned by VortexDesktop.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DesktopCanvas")
        self.setStyleSheet(DESKTOP_CANVAS)

        self._tick   = 0
        self._scan_y = 0.0

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_animation)
        self._anim_timer.start(33)

        self._build_ui()

    def _build_ui(self):
        """
        Only places the branding labels.
        No terminal, no widgets — those belong to VortexDesktop.
        """
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_brand = QLabel("VORTEX")
        lbl_brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_brand.setStyleSheet(DESKTOP_BRAND_LABEL)

        lbl_sub = QLabel("INITIALIZE  ·  DOMINATE  ·  EVOLVE")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(DESKTOP_SUB_LABEL)

        layout.addStretch(2)
        layout.addWidget(lbl_brand)
        layout.addWidget(lbl_sub)
        layout.addStretch(3)

        self.setLayout(layout)
        # ← NO terminal creation here. Ever.
        

    def _tick_animation(self):
        self._tick   += 1
        self._scan_y  = (self._scan_y + 0.002) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Background
        painter.fillRect(0, 0, w, h, QColor("#07070f"))

        # 2. Dot grid
        dot_spacing = 28
        dot_radius  = 1.2
        cols        = w // dot_spacing + 2
        rows        = h // dot_spacing + 2

        for row in range(rows):
            for col in range(cols):
                x          = col * dot_spacing
                y          = row * dot_spacing
                phase      = (col + row) * 0.3 + self._tick * 0.05
                brightness = (math.sin(phase) + 1.0) / 2.0
                intensity  = int(8 + brightness * 32)
                color      = QColor(0, intensity, intensity)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(x, y), dot_radius, dot_radius)

        # 3. Scan line
        scan_y_px = int(self._scan_y * h)
        painter.fillRect(0, scan_y_px, w, 2, QColor(0, 255, 255, 18))

        # 4. Vignette
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 80))
        gradient.setColorAt(0.3, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.7, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 80))
        painter.fillRect(0, 0, w, h, gradient)

    def contextMenuEvent(self, event):
        """Right-click opens the desktop context menu."""
        desktop = self._find_desktop()
        if desktop is None:
            return

        from themes.theme_engine import THEMES, get_engine
        get_engine()  # ensure engine is initialised

        theme_list = []
        for name in THEMES:
            def make_cb(n=name):
                return lambda: desktop._switch_theme(n)
            theme_list.append((name, make_cb()))

        callbacks = {
            "terminal":    lambda: desktop._handle_action("terminal"),
            "clock":       lambda: desktop._handle_action("clock"),
            "calendar":    lambda: desktop._handle_action("calendar"),
            "monitor":     lambda: desktop._handle_action("monitor"),
            "fullscreen":  desktop._toggle_fullscreen,
            "hide_desktop":desktop.hide,
            "theme_list":  theme_list,
        }

        menu = build_context_menu(self, callbacks)
        menu.exec(event.globalPos())

    def _find_desktop(self):
        """Walks up the parent chain to find VortexDesktop."""
        p = self.parent()
        while p is not None:
            if isinstance(p, VortexDesktop):
                return p
            p = p.parent() if callable(getattr(p, 'parent', None)) else None
        return None


# ─────────────────────────────────────────────────────────
#  VORTEX DESKTOP
#  Main window. Owns everything.
#  DesktopCanvas = background only.
#  TabTerminal   = floating over central widget.
# ─────────────────────────────────────────────────────────

class VortexDesktop(QMainWindow):
    """
    The VORTEX OS main desktop window.

    Owns:
    - TopBar
    - SidebarDock
    - DesktopCanvas  (background, animation)
    - BottomTaskbar
    - TabTerminal    (floating, hidden by default)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VORTEX OS")
        self._open_apps = []
        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self.showFullScreen()

    # ─────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #07070f;")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top bar
        self.topbar = TopBar()

        # Middle: sidebar + canvas
        middle        = QWidget()
        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        self.sidebar = SidebarDock()
        self.canvas  = DesktopCanvas()   # background only

        middle_layout.addWidget(self.sidebar)
        middle_layout.addWidget(self.canvas, 1)
        middle.setLayout(middle_layout)

        # Bottom taskbar
        self.taskbar = BottomTaskbar()

        # Assemble root
        root_layout.addWidget(self.topbar)
        root_layout.addWidget(middle, 1)
        root_layout.addWidget(self.taskbar)
        central.setLayout(root_layout)

        # TabTerminal — child of central widget so it floats
        # over the whole desktop area, not locked inside canvas
        self.terminal = TabTerminal(central)
        self.terminal.hide()

        from gui.app_launcher import AppLauncherPanel
        self.launcher = AppLauncherPanel(central)
        self.launcher.hide()
        self.launcher.app_launch_requested.connect(self._launch_app)

        # Position after layout is ready
        QTimer.singleShot(100, self._position_terminal)


    def _launch_app(self, app_id):
     """Requests app launch via AppManager signal (thread-safe)."""
     from core.app_manager import get_app_manager
     manager = get_app_manager()
     if manager:
        manager.app_launch_requested.emit(app_id)
    

    def _position_terminal(self):
        """
        Positions the terminal in the lower-right of the canvas area.
        Uses central widget geometry with offsets for bars.
        """
        central  = self.centralWidget()
        c_w      = central.width()  or 1200
        c_h      = central.height() or 800

        top_h    = self.topbar.height()
        side_w   = self.sidebar.width()
        bot_h    = self.taskbar.height()

        avail_w  = c_w - side_w
        avail_h  = c_h - top_h - bot_h

        term_w   = min(720, avail_w - 40)
        term_h   = min(480, avail_h - 40)
        term_x   = side_w  + (avail_w - term_w) - 20
        term_y   = top_h   + (avail_h - term_h) - 20

        self.terminal.setGeometry(term_x, term_y, term_w, term_h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'terminal'):
            self._position_terminal()

    # ─────────────────────────────────────────────
    #  SIGNALS
    # ─────────────────────────────────────────────

    def _connect_signals(self):
        self.sidebar.app_launched.connect(self._handle_action)
        self.taskbar.action_requested.connect(self._handle_action)
        self.terminal.closed.connect(self._on_terminal_closed)

    def _setup_shortcuts(self):
        # Ctrl+T: show terminal OR add new tab if already visible
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(
            self._handle_ctrl_t
        )
        # F11: toggle fullscreen
        QShortcut(QKeySequence("F11"), self).activated.connect(
            self._toggle_fullscreen
        )
        # Ctrl+Q: hide desktop (console keeps running)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(
            self.hide
        )
        # Ctrl+Shift+Q: full intentional quit with confirmation
        QShortcut(QKeySequence("Ctrl+Shift+Q"), self).activated.connect(
            self._full_quit
        )

    # ─────────────────────────────────────────────
    #  ACTION HANDLERS
    # ─────────────────────────────────────────────

    def _handle_action(self, action):
        """Central dispatcher for all sidebar and taskbar actions."""
        from core.app_manager import get_app_manager
        manager = get_app_manager()

        if action == "terminal":
            self._toggle_terminal()

        elif action == "clock":
            if manager:
                manager.request_widget("clock")
            self._add_open_app("CLOCK")
            self.sidebar.update_indicator("clock", True)

        elif action == "calendar":
            if manager:
                manager.request_widget("calendar")
            self._add_open_app("CALENDAR")
            self.sidebar.update_indicator("calendar", True)

        elif action == "monitor":
            if manager:
                manager.request_widget("monitor")
            self._add_open_app("MONITOR")
            self.sidebar.update_indicator("scan", True)

        elif action == "scan":
            # Show terminal and pre-fill 'scan' into the active tab
            self._show_terminal()
            self._prefill_active_tab("scan")

        elif action == "theme":
            # Show terminal and pre-fill 'theme '
            self._show_terminal()
            self._prefill_active_tab("theme ")

        elif action == "desktop":
            self.launcher.toggle()
            self.terminal.hide()
            self._remove_open_app("TERMINAL")

    def _prefill_active_tab(self, text):
        """
        Pre-fills the input line of the currently active tab.
        TabTerminal has a stack — we get the current widget from it.
        """
        idx    = self.terminal.stack.currentIndex()
        widget = self.terminal.stack.widget(idx)
        if widget and hasattr(widget, 'input_line'):
            widget.input_line.setText(text)
            widget.input_line.setFocus()

    def _handle_ctrl_t(self):
        """
        Ctrl+T behaviour:
        - Terminal hidden  → show it (focuses existing first tab)
        - Terminal visible → open a new tab
        """
        if self.terminal.isVisible():
            self.terminal.add_tab()
        else:
            self._show_terminal()

    def _show_terminal(self):
        """Shows the terminal panel and focuses the active tab input."""
        self._position_terminal()
        self.terminal.show()
        self.terminal.raise_()
        self._add_open_app("TERMINAL")
        self.sidebar.set_active("terminal")
        self.sidebar.update_indicator("terminal", True)

        # Focus the input of the currently visible tab
        QTimer.singleShot(50, self._focus_active_tab)

    def _focus_active_tab(self):
        """Focuses the input line of the active tab."""
        idx    = self.terminal.stack.currentIndex()
        widget = self.terminal.stack.widget(idx)
        if widget and hasattr(widget, 'input_line'):
            widget.input_line.setFocus()

    def _toggle_terminal(self):
        """Shows or hides the terminal panel."""
        if self.terminal.isVisible():
            self.terminal.hide()
            self._remove_open_app("TERMINAL")
            self.sidebar.set_active(None)
            self.sidebar.update_indicator("terminal", False)
        else:
            self._show_terminal()

    def _on_terminal_closed(self):
        """Called when the terminal panel's × button is clicked."""
        self._remove_open_app("TERMINAL")
        self.sidebar.set_active(None)
        self.sidebar.update_indicator("terminal", False)

    # ─────────────────────────────────────────────
    #  THEME
    # ─────────────────────────────────────────────

    def _switch_theme(self, theme_name):
        from themes.theme_engine import get_engine
        get_engine().set_theme(theme_name)
        self._show_status("THEME CHANGED", theme_name.upper())

    def _show_status(self, title, message):
        """Prints status to console. No GUI toast required."""
        print(f"\n  ◈ {title}  —  {message}\n")

    # ─────────────────────────────────────────────
    #  OPEN APP TRACKING
    # ─────────────────────────────────────────────

    def _add_open_app(self, name):
        if name not in self._open_apps:
            self._open_apps.append(name)
        self.taskbar.set_open_apps(self._open_apps)

    def _remove_open_app(self, name):
        if name in self._open_apps:
            self._open_apps.remove(name)
        self.taskbar.set_open_apps(self._open_apps)

    # ─────────────────────────────────────────────
    #  WINDOW MANAGEMENT
    # ─────────────────────────────────────────────

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def _full_quit(self):
        """Ctrl+Shift+Q — full quit with confirmation dialog."""
        reply = QMessageBox.question(
            self,
            "Quit VORTEX OS",
            "Shut down VORTEX OS completely?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()

    def closeEvent(self, event):
        """
        Closing the window hides it instead of destroying it.
        The console terminal and Qt event loop keep running.
        Type 'desktop' in the console to restore.
        """
        event.ignore()
        self.hide()
        print("\n[VORTEX] Desktop hidden. Type 'desktop' to restore.\n")