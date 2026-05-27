# gui/app_launcher.py
# VORTEX OS - Slide-out App Launcher Panel

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QScrollArea
)
from PyQt6.QtCore    import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui     import QFont


class AppLauncherPanel(QWidget):
    """
    A panel that slides in from the left showing all installed apps.

    Triggered by clicking the ⬡ (desktop) button in the sidebar.
    Each app appears as an icon button in a grid.
    Clicking an app launches it via AppManager signal.

    Animation: slides in/out horizontally using QPropertyAnimation.
    """

    app_launch_requested = pyqtSignal(str)   # str = app_id

    WIDTH   = 280
    VISIBLE = 56     # sidebar width (starting X when hidden)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.WIDTH)
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0a14;
                border-right: 1px solid #1a1a2e;
            }
        """)

        self._visible = False
        self._build_ui()

        # Start hidden (off-screen to the left)
        if parent:
            self.move(self.VISIBLE - self.WIDTH, 0)
            self.resize(self.WIDTH, parent.height())

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("◈  APPS")
        header.setFixedHeight(40)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "color:#00ffff;font-size:11px;font-weight:bold;"
            "letter-spacing:4px;background:#0d0d1a;"
            "border-bottom:1px solid #003333;"
        )

        # Scrollable app grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea{border:none;background:transparent;}"
        )
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background:transparent;")
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setSpacing(8)
        self.grid_container.setLayout(self.grid_layout)
        scroll.setWidget(self.grid_container)

        layout.addWidget(header)
        layout.addWidget(scroll, 1)
        self.setLayout(layout)

    def populate(self):
        """
        Clears and redraws the app grid from the registry.
        Called every time the panel is shown so it's always current.
        """
        # Clear existing buttons
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        from apps.registry import get_registry
        registry = get_registry()
        apps     = registry.get_all()

        if not apps:
            lbl = QLabel("No apps installed.")
            lbl.setStyleSheet("color:#333355;font-size:11px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(lbl, 0, 0, 1, 2)
            return

        # 2 columns of app buttons
        for idx, app in enumerate(apps):
            row = idx // 2
            col = idx  % 2
            btn = self._make_app_button(app)
            self.grid_layout.addWidget(btn, row, col)

    def _make_app_button(self, app):
        """Creates a styled icon button for one app."""
        icon    = app.get("icon", "◈")
        name    = app.get("name", app["id"])
        app_id  = app["id"]

        btn = QPushButton(f"{icon}\n{name}")
        btn.setFixedSize(112, 80)
        btn.setFont(QFont("monospace", 10))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0d0d1a;
                color: #888899;
                border: 1px solid #1a1a2e;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #1a1a2e;
                color: #00ffff;
                border-color: #00ffff;
            }
            QPushButton:pressed {
                background-color: #003333;
            }
        """)
        btn.clicked.connect(
            lambda checked=False, aid=app_id:
                self.app_launch_requested.emit(aid)
        )
        return btn

    def toggle(self):
        """Slides the panel in or out."""
        if self._visible:
            self.slide_out()
        else:
            self.populate()
            self.slide_in()

    def slide_in(self):
        """Animates the panel sliding into view."""
        if self.parent():
            self.resize(self.WIDTH, self.parent().height())
        self.show()
        self.raise_()

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(250)
        anim.setStartValue(self.pos())
        anim.setEndValue(
            self.pos().__class__(self.VISIBLE, self.pos().y())
        )
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim    = anim   # Keep reference
        self._visible = True

    def slide_out(self):
        """Animates the panel sliding out of view."""
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(200)
        anim.setStartValue(self.pos())
        anim.setEndValue(
            self.pos().__class__(
                self.VISIBLE - self.WIDTH,
                self.pos().y()
            )
        )
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.hide)
        anim.start()
        self._anim    = anim
        self._visible = False