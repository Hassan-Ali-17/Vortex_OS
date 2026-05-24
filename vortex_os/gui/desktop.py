# gui/desktop.py
# VORTEX OS - Main Desktop Environment Window
from gui.context_menu  import build_context_menu
from themes.theme_engine import THEMES
import os
import math

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QApplication
)
from PyQt6.QtCore  import Qt, QTimer, QPointF
from PyQt6.QtGui   import (
    QPainter, QColor, QPen, QBrush,
    QLinearGradient, QKeySequence, QShortcut
)

from gui.topbar        import TopBar
from gui.sidebar       import SidebarDock
from gui.taskbar       import BottomTaskbar
from gui.terminal_widget import EmbeddedTerminal
from gui.styles        import DESKTOP_CANVAS, DESKTOP_BRAND_LABEL, DESKTOP_SUB_LABEL


class DesktopCanvas(QWidget):
    """
    The main desktop area — draws the animated cyberpunk background.

    Animation:
    - A grid of dots pulses in brightness using a sine wave
    - Slow scan line drifts downward
    - Subtle vignette darkens the edges

    All drawing happens in paintEvent using QPainter.
    A QTimer drives the animation at ~30 FPS.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DesktopCanvas")
        self.setStyleSheet(DESKTOP_CANVAS)

        # Animation state
        self._tick       = 0       # Increments every frame
        self._scan_y     = 0.0     # Scan line Y position (0.0–1.0)

        # Animation timer — 33ms ≈ 30 FPS
        # Low enough to be smooth, high enough to stay lightweight
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_animation)
        self._anim_timer.start(33)

        self._build_ui()

    def _build_ui(self):
        """Places branding labels centered on the canvas."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Large VORTEX text (dim — sits behind widgets)
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

    def contextMenuEvent(self, event):
     """
     Called by Qt when the user right-clicks on the canvas.
     We build the menu with callbacks into the desktop, then show it.
     """
     # Walk up to find the VortexDesktop parent
     desktop = self._find_desktop()
     if desktop is None:
        return

     from themes.theme_engine import THEMES, get_engine

    # Build theme switcher entries
     engine     = get_engine()
     theme_list = []
     for name in THEMES:
        # Capture name in lambda default arg
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
        p = p.parent() if hasattr(p, 'parent') else None
     return None    

    def _tick_animation(self):
        """Advances the animation state and triggers a repaint."""
        self._tick   += 1
        self._scan_y  = (self._scan_y + 0.002) % 1.0
        self.update()   # Schedules paintEvent

    def paintEvent(self, event):
        """
        Draws the animated background.

        Draw order (back to front):
        1. Solid dark background
        2. Dot grid with pulsing brightness
        3. Horizontal scan line
        4. Vignette overlay
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # ── 1. Background ─────────────────────────
        painter.fillRect(0, 0, w, h, QColor("#07070f"))

        # ── 2. Dot grid ───────────────────────────
        dot_spacing = 28
        dot_radius  = 1.2

        cols = w // dot_spacing + 2
        rows = h // dot_spacing + 2

        for row in range(rows):
            for col in range(cols):
                x = col * dot_spacing
                y = row * dot_spacing

                # Sine wave pulse — each dot has a phase offset
                # based on its position, creating a ripple effect
                phase     = (col + row) * 0.3 + self._tick * 0.05
                brightness = (math.sin(phase) + 1.0) / 2.0   # 0.0–1.0

                # Map brightness to color intensity (8–40 out of 255)
                intensity = int(8 + brightness * 32)
                color     = QColor(0, intensity, intensity)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(
                    QPointF(x, y),
                    dot_radius, dot_radius
                )

        # ── 3. Scan line ──────────────────────────
        scan_y_px = int(self._scan_y * h)
        scan_color = QColor(0, 255, 255, 18)   # Very transparent cyan
        painter.fillRect(0, scan_y_px, w, 2, scan_color)

        # ── 4. Vignette (edge darkening) ──────────
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0.0,  QColor(0, 0, 0, 80))
        gradient.setColorAt(0.3,  QColor(0, 0, 0, 0))
        gradient.setColorAt(0.7,  QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0,  QColor(0, 0, 0, 80))
        painter.fillRect(0, 0, w, h, gradient)


class VortexDesktop(QMainWindow):
    """
    The main VORTEX OS desktop window.

    Assembles all components:
    - TopBar
    - SidebarDock + DesktopCanvas (side by side)
    - BottomTaskbar

    Manages:
    - Terminal show/hide toggle
    - Widget launching via AppManager
    - Keyboard shortcuts
    - Open app tracking for taskbar
      """

    def _show_status(self, title, message):
     """
    Lightweight status output — prints to console instead of
    using the notification system.
    Keeps the code working without any GUI toast dependency.
     """
     print(f"\n  ◈ {title}  —  {message}\n")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VORTEX OS")

        # Track which widgets are open (for taskbar display)
        self._open_apps = []

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()

        # Start fullscreen
        self.showFullScreen()

    def _build_ui(self):
        """Assembles the full desktop layout."""

        # ── Central widget (everything sits inside this) ──
        central = QWidget()
        central.setStyleSheet("background-color: #07070f;")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top bar ───────────────────────────────
        self.topbar = TopBar()

        # ── Middle row: sidebar + canvas ──────────
        middle = QWidget()
        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        self.sidebar = SidebarDock()

        # Canvas holds the animated background AND the terminal
        self.canvas = DesktopCanvas()

        # Terminal widget — created but hidden initially
        self.terminal = EmbeddedTerminal(self.canvas)
        self.terminal.hide()
        self._position_terminal()

        middle_layout.addWidget(self.sidebar)
        middle_layout.addWidget(self.canvas, 1)   # stretch=1: takes remaining space
        middle.setLayout(middle_layout)

        # ── Bottom taskbar ─────────────────────────
        self.taskbar = BottomTaskbar()

        # ── Assemble root layout ───────────────────
        root_layout.addWidget(self.topbar)
        root_layout.addWidget(middle, 1)
        root_layout.addWidget(self.taskbar)

        central.setLayout(root_layout)

    def _position_terminal(self):
        """
        Places the terminal widget in the lower-right area of the canvas.
        Called on first show and on window resize.
        """
        canvas_w = self.canvas.width()  or 1200
        canvas_h = self.canvas.height() or 800

        term_w = min(700, canvas_w - 40)
        term_h = min(450, canvas_h - 40)
        term_x = canvas_w - term_w - 20
        term_y = canvas_h - term_h - 20

        self.terminal.setGeometry(term_x, term_y, term_w, term_h)

    def resizeEvent(self, event):
        """Reposition terminal when window resizes."""
        super().resizeEvent(event)
        self._position_terminal()

    def _connect_signals(self):
        """Connects all signals to their slots."""
        self.sidebar.app_launched.connect(self._handle_action)
        self.taskbar.action_requested.connect(self._handle_action)
        self.terminal.closed.connect(self._on_terminal_closed)

    def _setup_shortcuts(self):
    # Ctrl+T — toggle terminal
     sc_terminal = QShortcut(QKeySequence("Ctrl+T"), self)
     sc_terminal.activated.connect(
        lambda: self._handle_action("terminal")
     )

    # F11 — toggle fullscreen
     sc_fs = QShortcut(QKeySequence("F11"), self)
     sc_fs.activated.connect(self._toggle_fullscreen)

    # Ctrl+Q now just HIDES the desktop — does NOT quit anything
     sc_hide = QShortcut(QKeySequence("Ctrl+Q"), self)
     sc_hide.activated.connect(self.hide)

    # Ctrl+Shift+Q — full application quit (intentional, explicit)
     sc_quit = QShortcut(QKeySequence("Ctrl+Shift+Q"), self)
     sc_quit.activated.connect(self._full_quit)

    def _full_quit(self):
     """
    Ctrl+Shift+Q — intentional full quit.
    Confirms before killing everything.
     """
     from PyQt6.QtWidgets import QMessageBox
     reply = QMessageBox.question(
        self,
        "Quit VORTEX OS",
        "Shut down VORTEX OS completely?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
     )
     if reply == QMessageBox.StandardButton.Yes:
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def _handle_action(self, action):
        """
        Central dispatcher for sidebar and taskbar actions.
        """
        from core.app_manager import get_app_manager

        if action == "terminal":
            self._toggle_terminal()

        elif action == "clock":
            manager = get_app_manager()
            if manager:
                manager.request_widget("clock")
            self._add_open_app("CLOCK")
            self.sidebar.update_indicator("clock", True)   

        elif action == "calendar":
            manager = get_app_manager()
            if manager:
                manager.request_widget("calendar")
            self._add_open_app("CALENDAR")
            self.sidebar.update_indicator("calendar", True)        # ← ADD


        elif action == "scan":
            self._toggle_terminal()
            # Pre-fill the input with 'scan'
            self.terminal.input_line.setText("scan")
            self.terminal.input_line.setFocus()

        elif action == "theme":
            self._toggle_terminal()
            self.terminal.input_line.setText("theme ")
            self.terminal.input_line.setFocus()

        elif action == "desktop":
            # Hide all floating elements, show clean desktop
            self.terminal.hide()
            self._remove_open_app("TERMINAL")
        elif action == "monitor":
          manager = get_app_manager()
          if manager:
           manager.request_widget("monitor")
        self._add_open_app("MONITOR")  
        self.sidebar.update_indicator("scan", True)            # ← ADD 

    def _toggle_terminal(self):
     if self.terminal.isVisible():
        self.terminal.hide()
        self._remove_open_app("TERMINAL")
        self.sidebar.set_active(None)
        self.sidebar.update_indicator("terminal", False)   # ← ADD
     else:
        self._position_terminal()
        self.terminal.show()
        self.terminal.raise_()
        self.terminal.input_line.setFocus()
        self._add_open_app("TERMINAL")
        self.sidebar.set_active("terminal")
        self.sidebar.update_indicator("terminal", True)    # ← ADD

    def _switch_theme(self, theme_name):
     """
    Switches the active theme and reports to console.
    No notification widget required.
    """
     from themes.theme_engine import get_engine
     engine = get_engine()
     engine.set_theme(theme_name)
     self._show_status("THEME CHANGED", theme_name.upper())        

    def _on_terminal_closed(self):
        """Called when the terminal's X button is clicked."""
        self._remove_open_app("TERMINAL")
        self.sidebar.set_active(None)
        self.sidebar.update_indicator("terminal", False)       # ← ADD


    def _add_open_app(self, name):
        """Adds an app name to the taskbar open-apps list."""
        if name not in self._open_apps:
            self._open_apps.append(name)
        self.taskbar.set_open_apps(self._open_apps)

    def _remove_open_app(self, name):
        """Removes an app name from the taskbar open-apps list."""
        if name in self._open_apps:
            self._open_apps.remove(name)
        self.taskbar.set_open_apps(self._open_apps)

    def _toggle_fullscreen(self):
        """Toggles between fullscreen and maximized window."""
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
     """
    Override closeEvent so closing the desktop window
    does NOT kill the Qt application or the terminal thread.
    It just hides the window. The console terminal keeps running.
     """
     event.ignore()        # Block the default close behaviour
     self.hide()           # Just hide — don't destroy
     print("\n[VORTEX] Desktop hidden. Type 'desktop' to restore it.\n")

    def _quit_desktop(self):
     """
    Ctrl+Q — hides desktop only. Terminal stays alive.
    Previously this called self.close() which propagated to app.quit().
     """
     self.hide()