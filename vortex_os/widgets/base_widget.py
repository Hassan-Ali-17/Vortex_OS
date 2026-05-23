# widgets/base_widget.py
# VORTEX OS - Base Widget Class
# All floating widgets inherit from this.

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore    import Qt, QPoint
from PyQt6.QtGui     import QPainter, QColor, QPen, QFont


class BaseWidget(QWidget):
    """
    Base class for all VORTEX OS floating widgets.

    Provides:
    - Frameless, always-on-top window
    - Click-to-drag anywhere on the widget
    - Cyberpunk dark background with colored border
    - Escape key to close
    - Semi-transparent background

    Child classes override:
    - setup_ui()    : build the layout and child widgets
    - get_title()   : window title string
    - BORDER_COLOR  : hex color string for the border glow
    """

    # Default geometry — child classes can override
    DEFAULT_X      = 100
    DEFAULT_Y      = 100
    DEFAULT_WIDTH  = 300
    DEFAULT_HEIGHT = 200

    # Colors — cyberpunk defaults, overridden by child classes
    BACKGROUND_COLOR = "#0a0a0f"     # Near-black
    BORDER_COLOR     = "#00ffff"     # Cyan
    BORDER_WIDTH     = 2

    def __init__(self, parent=None):
        super().__init__(parent)

        # Track mouse position for drag calculation
        self._drag_start_position = QPoint()
        self._dragging = False

        self._init_window()
        self.setup_ui()

    def _init_window(self):
        """
        Configures the window flags and geometry.

        Flag explanations:
        FramelessWindowHint  → no title bar, no OS chrome
        WindowStaysOnTopHint → floats above other windows
        Tool                 → doesn't appear in taskbar
        """
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint      |
            Qt.WindowType.WindowStaysOnTopHint     |
            Qt.WindowType.Tool
        )

        # Allow background transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set position and size
        self.setGeometry(
            self.DEFAULT_X,
            self.DEFAULT_Y,
            self.DEFAULT_WIDTH,
            self.DEFAULT_HEIGHT
        )

        # Window title (shows in alt-tab even for frameless windows)
        self.setWindowTitle(self.get_title())

    def get_title(self):
        """Override in child class to set window title."""
        return "VORTEX Widget"

    def setup_ui(self):
        """Override in child class to build the UI layout."""
        pass

    def paintEvent(self, event):
        """
        Draws the custom background and border.

        PyQt6's paintEvent is called every time the widget needs
        to be redrawn (on show, resize, theme change, etc.).

        We draw:
        1. Semi-transparent dark background rectangle
        2. Colored border rectangle around the edge
        3. Corner accent marks (cyberpunk detail)
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # ── Background ──────────────────────────────
        bg_color = QColor(self.BACKGROUND_COLOR)
        bg_color.setAlpha(230)   # Slight transparency (0=invisible, 255=solid)
        painter.fillRect(0, 0, w, h, bg_color)

        # ── Border ──────────────────────────────────
        border_color = QColor(self.BORDER_COLOR)
        pen = QPen(border_color, self.BORDER_WIDTH)
        painter.setPen(pen)
        painter.drawRect(
            self.BORDER_WIDTH,
            self.BORDER_WIDTH,
            w - self.BORDER_WIDTH * 2,
            h - self.BORDER_WIDTH * 2
        )

        # ── Corner accents (small L-shapes at each corner) ──
        accent_len = 12    # Length of each corner tick
        corner_pen = QPen(border_color, 3)
        painter.setPen(corner_pen)

        margin = self.BORDER_WIDTH + 4

        # Top-left
        painter.drawLine(margin, margin, margin + accent_len, margin)
        painter.drawLine(margin, margin, margin, margin + accent_len)

        # Top-right
        painter.drawLine(w - margin, margin, w - margin - accent_len, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + accent_len)

        # Bottom-left
        painter.drawLine(margin, h - margin, margin + accent_len, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - accent_len)

        # Bottom-right
        painter.drawLine(w - margin, h - margin, w - margin - accent_len, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - accent_len)

    # ── Drag support ────────────────────────────────────────

    def mousePressEvent(self, event):
        """Records position when user clicks the widget."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.globalPosition().toPoint()
            self._dragging = True

    def mouseMoveEvent(self, event):
        """Moves the window as the mouse drags."""
        if self._dragging:
            delta = event.globalPosition().toPoint() - self._drag_start_position
            self.move(self.pos() + delta)
            self._drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """Stops dragging."""
        self._dragging = False

    def keyPressEvent(self, event):
        """Escape closes the widget."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
     """
    Called when the widget is closed (ESC or window manager).
    Stops all child timers before the widget is destroyed.
    This prevents the 'timer stopped from another thread' warning.
     """
    # Stop all QTimer children of this widget
     from PyQt6.QtCore import QTimer
     for timer in self.findChildren(QTimer):
        timer.stop()
     event.accept()
     super().closeEvent(event) if hasattr(super(), 'closeEvent') else None     