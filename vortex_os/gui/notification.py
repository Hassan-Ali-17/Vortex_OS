# gui/notification.py
# VORTEX OS - Toast Notification System
# Animated slide-in/fade-out toast messages.

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore    import (
    Qt, QTimer, QPropertyAnimation,
    QEasingCurve, QPoint, QRect,
    pyqtProperty
)
from PyQt6.QtGui     import QPainter, QColor


class ToastNotification(QWidget):
    """
    A single animated toast notification.

    Lifecycle:
    1. Created hidden, positioned off-screen to the right
    2. slide_in()  : animates position from off-screen → visible
    3. Stays visible for `duration` milliseconds
    4. slide_out() : animates position back off-screen + fades
    5. Destroys itself when animation finishes

    Why inherit QWidget not QLabel?
    We need a custom paintEvent for the styled background,
    and we need to hold multiple child labels.
    """

    def __init__(self, title, message, parent=None,
                 duration=3000, color="#00ffff"):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._duration   = duration
        self._color      = color
        self._opacity    = 1.0

        # Fixed size for the toast
        self.setFixedSize(280, 60)

        self._build_ui(title, message)

    def _build_ui(self, title, message):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"color: {self._color}; font-size: 11px; "
            f"font-weight: bold; font-family: monospace; "
            f"letter-spacing: 1px; background: transparent;"
        )

        lbl_msg = QLabel(message)
        lbl_msg.setStyleSheet(
            "color: #888899; font-size: 10px; "
            "font-family: monospace; background: transparent;"
        )

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_msg)
        self.setLayout(layout)

    def paintEvent(self, event):
        """Custom background: dark panel with colored left border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Semi-transparent dark background
        bg = QColor("#0d0d1a")
        bg.setAlpha(230)
        painter.fillRect(0, 0, w, h, bg)

        # Colored left accent bar
        accent = QColor(self._color)
        painter.fillRect(0, 0, 3, h, accent)

        # Bottom border line
        border = QColor(self._color)
        border.setAlpha(60)
        painter.fillRect(0, h - 1, w, 1, border)

    # ── qt property for opacity animation ─────────────────
    # We need a real Qt property (not just a Python attribute)
    # so QPropertyAnimation can animate it.

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)

    # pyqtProperty declares a real Qt property
    opacity = pyqtProperty(float, fget=get_opacity, fset=set_opacity)

    def slide_in(self, start_pos, end_pos):
        """
        Animates the toast sliding in from start_pos to end_pos.
        After animation, starts the auto-dismiss timer.

        Args:
            start_pos: QPoint — where toast starts (off-screen right)
            end_pos:   QPoint — where toast ends (visible position)
        """
        self.move(start_pos)
        self.show()

        # Position animation
        self._anim_in = QPropertyAnimation(self, b"pos")
        self._anim_in.setDuration(300)
        self._anim_in.setStartValue(start_pos)
        self._anim_in.setEndValue(end_pos)
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_in.start()

        # After duration ms, slide out
        QTimer.singleShot(self._duration, self.slide_out)

    def slide_out(self):
        """
        Animates position back off-screen and fades opacity to 0.
        Uses QPropertyAnimation on both pos and opacity simultaneously.
        """
        if not self.isVisible():
            return

        parent_width = self.parent().width() if self.parent() else 1920
        off_right    = QPoint(parent_width + 10, self.pos().y())

        # Position animation (slide right)
        self._anim_out = QPropertyAnimation(self, b"pos")
        self._anim_out.setDuration(250)
        self._anim_out.setStartValue(self.pos())
        self._anim_out.setEndValue(off_right)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InCubic)

        # Opacity animation (fade out)
        self._anim_fade = QPropertyAnimation(self, b"opacity")
        self._anim_fade.setDuration(250)
        self._anim_fade.setStartValue(1.0)
        self._anim_fade.setEndValue(0.0)

        # Close widget when fade finishes
        self._anim_fade.finished.connect(self.close)

        self._anim_out.start()
        self._anim_fade.start()


class NotificationManager:
    """
    Manages a stack of toast notifications.

    Notifications stack vertically — each new one appears
    below the previous ones, offset by the toast height + gap.

    Usage:
        manager = NotificationManager(parent_widget)
        manager.show("◈ Command Done", "scan  ·  0.42s", color="#00ff88")
    """

    TOAST_HEIGHT  = 60
    TOAST_GAP     = 8
    TOP_MARGIN    = 50    # Below the top bar
    RIGHT_MARGIN  = 12

    def __init__(self, parent):
        self._parent  = parent
        self._active  = []   # List of currently visible toasts

    def show(self, title, message, duration=3000, color="#00ffff"):
        """
        Creates and shows a new toast notification.
        Stacks below any existing ones.
        """
        parent_w = self._parent.width()
        toast_x  = parent_w - ToastNotification.width
        slot     = len(self._active)

        toast = ToastNotification(
            title, message,
            parent=self._parent,
            duration=duration,
            color=color
        )

        # Calculate vertical position based on how many are active
        y_pos = self.TOP_MARGIN + slot * (self.TOAST_HEIGHT + self.TOAST_GAP)

        # Start position: off-screen to the right
        start_pos = QPoint(
            self._parent.width() + 10,
            y_pos
        )
        # End position: visible, right-aligned with margin
        end_pos = QPoint(
            self._parent.width() - toast.width() - self.RIGHT_MARGIN,
            y_pos
        )

        self._active.append(toast)

        # When toast closes, remove it from our list
        toast.destroyed.connect(lambda: self._on_toast_closed(toast))

        toast.slide_in(start_pos, end_pos)

    def _on_toast_closed(self, toast):
        """Removes a closed toast from the active list."""
        if toast in self._active:
            self._active.remove(toast)
        # Re-stack remaining toasts
        self._restack()

    def _restack(self):
        """
        Smoothly repositions remaining toasts after one closes.
        Each toast animates to its new position.
        """
        for i, toast in enumerate(self._active):
            if not toast.isVisible():
                continue
            target_y = self.TOP_MARGIN + i * (self.TOAST_HEIGHT + self.TOAST_GAP)
            target_x = self._parent.width() - toast.width() - self.RIGHT_MARGIN

            anim = QPropertyAnimation(toast, b"pos")
            anim.setDuration(200)
            anim.setStartValue(toast.pos())
            anim.setEndValue(QPoint(target_x, target_y))
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            anim.start()
            # Keep reference so Python doesn't GC it before it finishes
            toast._restack_anim = anim