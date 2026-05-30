# gui/login_screen.py
# VORTEX OS - Login Screen
# Fullscreen login window with shake animation and lockout.

import os
import json
import hashlib
import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QApplication, QGraphicsOpacityEffect
)
from PyQt6.QtCore    import (
    Qt, QTimer, QPropertyAnimation,
    QEasingCurve, pyqtSignal, QPoint
)
from PyQt6.QtGui     import (
    QPainter, QColor, QFont,
    QLinearGradient, QBrush
)

SESSION_FILE = "config/session.json"


def _hash_password(password):
    """
    Hashes a password using SHA-256.
    We add a fixed salt to prevent rainbow table attacks.
    """
    salt   = "VORTEX_OS_SALT_2025"
    salted = salt + password + salt
    return hashlib.sha256(salted.encode()).hexdigest()


def _load_session():
    """Loads session config from JSON."""
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "username":      "vortex",
            "password_hash": "",
            "display_name":  "VORTEX USER",
            "auto_login":    False,
            "max_attempts":  5,
            "session_active":False,
        }


def _save_session(data):
    """Saves session config to JSON."""
    try:
        os.makedirs("config", exist_ok=True)
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[Session] Save error: {e}")


class AvatarWidget(QWidget):
    """
    Draws a glowing circular avatar with the user's initials.
    Pure QPainter — no image files needed.
    """

    def __init__(self, initials="VX", parent=None):
        super().__init__(parent)
        self.initials = initials
        self.setFixedSize(96, 96)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2
        r  = min(w, h) // 2 - 4

        # Outer glow ring
        from PyQt6.QtGui import QPen
        glow_pen = QPen(QColor(0, 255, 255, 40), 8)
        p.setPen(glow_pen)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Inner glow ring
        glow_pen2 = QPen(QColor(0, 255, 255, 80), 3)
        p.setPen(glow_pen2)
        p.drawEllipse(cx - r + 4, cy - r + 4,
                      (r - 4) * 2, (r - 4) * 2)

        # Filled circle background
        grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.setColorAt(0.0, QColor("#0d0d2a"))
        grad.setColorAt(1.0, QColor("#001a1a"))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - r + 2, cy - r + 2,
                      (r - 2) * 2, (r - 2) * 2)

        # Initials text
        font = QFont("monospace", 22, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor("#00ffff"))
        p.drawText(
            0, 0, w, h,
            Qt.AlignmentFlag.AlignCenter,
            self.initials.upper()[:2]
        )


class LoginScreen(QWidget):
    """
    Fullscreen VORTEX OS login screen.

    States:
    - FIRST_RUN  : no password set — prompts user to create one
    - LOGIN      : normal password entry
    - LOCKED     : too many failed attempts — shows countdown
    - SUCCESS    : correct password — emits login_successful

    Signals:
        login_successful : emitted when correct password entered
    """

    _THEME_HEX = {
    "cyberpunk": "#00ffff",
    "matrix":    "#00ff44",
    "blood":     "#ff3355",
    "ghost":     "#e0e0ff",
    "solar":     "#ffcc00",
    "arctic":    "#88ddff",
    }

    login_successful = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._session      = _load_session()
        self._attempts     = 0
        self._max_attempts = self._session.get("max_attempts", 5)
        self._locked       = False
        self._first_run    = not bool(
            self._session.get("password_hash", "")
        )
        from themes.theme_engine import THEMES
        self._theme_colors = []
        for theme_name, theme_data in THEMES.items():
         # Each theme stores colorama codes — we need hex colors.
         # We map theme names to their hex primary colors directly.
         self._theme_colors.append(
             self._THEME_HEX.get(theme_name, "#00ffff")
         )
        self._theme_idx      = 0
        self._current_color  = self._theme_colors[0]
        self._target_color   = self._theme_colors[0]
        self._transition_step = 0   # 0–20 steps per transition
        self._in_transition   = False

# Theme cycle timer — advances theme every 10 seconds
        self._slide_timer = QTimer(self)
        self._slide_timer.timeout.connect(self._next_theme_color)
        self._slide_timer.start(10000)

# Smooth transition timer — runs at 30fps during color change
        self._trans_timer = QTimer(self)
        self._trans_timer.timeout.connect(self._transition_tick)

        self._lock_timer   = None
        self._lock_secs    = 30   # Lockout duration

        # Animation tick for background
        self._tick         = 0
        self._anim_timer   = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_bg)
        self._anim_timer.start(33)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.showFullScreen()

        self._build_ui()

        # Auto-login check
        if self._session.get("auto_login", False) and not self._first_run:
            QTimer.singleShot(500, self._auto_login)

    def _build_ui(self):
        """Builds the login form layout."""
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Central card ───────────────────────────────────
        # The login form sits in a centered card widget
        self.card = QWidget()
        self.card.setFixedWidth(400)
        self.card.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 20, 220);
                border: 1px solid #003333;
                border-radius: 8px;
            }
        """)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── OS label ───────────────────────────────────────
        lbl_os = QLabel("VORTEX OS")
        lbl_os.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_os.setStyleSheet(
            "color: #00ffff; font-size: 13px; font-weight: bold;"
            "letter-spacing: 6px; border: none;"
        )

        # ── Avatar ─────────────────────────────────────────
        display_name = self._session.get("display_name", "VX")
        initials     = "".join(
            w[0] for w in display_name.split()[:2]
        ).upper() or "VX"

        avatar_row = QHBoxLayout()
        avatar_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar = AvatarWidget(initials)
        avatar_row.addWidget(self.avatar)

        # ── Display name ───────────────────────────────────
        self.lbl_name = QLabel(display_name)
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_name.setStyleSheet(
            "color: #e0e0ff; font-size: 16px; font-weight: bold;"
            "letter-spacing: 2px; border: none;"
        )

        # ── Username (dim) ─────────────────────────────────
        username = self._session.get("username", "vortex")
        lbl_user = QLabel(f"@{username}")
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_user.setStyleSheet(
            "color: #444466; font-size: 11px; "
            "font-family: monospace; border: none;"
        )

        # ── Password field ─────────────────────────────────
        pw_row = QHBoxLayout()
        pw_row.setSpacing(6)

        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setFixedHeight(42)
        self.pw_input.setStyleSheet("""
            QLineEdit {
                background-color: #0a0a14;
                color: #00ffff;
                border: 1px solid #003333;
                border-radius: 4px;
                padding: 8px 12px;
                font-family: monospace;
                font-size: 14px;
                letter-spacing: 3px;
            }
            QLineEdit:focus {
                border-color: #00ffff;
            }
        """)

        if self._first_run:
            self.pw_input.setPlaceholderText("Create a password...")
        else:
            self.pw_input.setPlaceholderText("Enter password...")

        self.pw_input.returnPressed.connect(self._on_submit)

        # Show/hide password button
        self.btn_show = QPushButton("👁")
        self.btn_show.setFixedSize(42, 42)
        self.btn_show.setCheckable(True)
        self.btn_show.setStyleSheet("""
            QPushButton {
                background: #0a0a14;
                color: #333355;
                border: 1px solid #003333;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:checked {
                color: #00ffff;
                border-color: #00ffff;
            }
            QPushButton:hover { border-color: #006666; }
        """)
        self.btn_show.toggled.connect(self._toggle_show)

        pw_row.addWidget(self.pw_input)
        pw_row.addWidget(self.btn_show)

        # ── Confirm password (first run only) ──────────────
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setFixedHeight(42)
        self.confirm_input.setPlaceholderText("Confirm password...")
        self.confirm_input.setStyleSheet(self.pw_input.styleSheet())
        self.confirm_input.returnPressed.connect(self._on_submit)
        self.confirm_input.setVisible(self._first_run)

        # ── Login button ───────────────────────────────────
        btn_label = "SET PASSWORD" if self._first_run else "UNLOCK"
        self.btn_login = QPushButton(btn_label)
        self.btn_login.setFixedHeight(44)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #003333;
                color: #00ffff;
                border: 1px solid #006666;
                border-radius: 4px;
                font-family: monospace;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 3px;
            }
            QPushButton:hover {
                background-color: #004444;
                border-color: #00ffff;
            }
            QPushButton:pressed {
                background-color: #006666;
            }
        """)
        self.btn_login.clicked.connect(self._on_submit)

        # ── Status label ───────────────────────────────────
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFixedHeight(24)
        self.lbl_status.setStyleSheet(
            "color: #ff3355; font-size: 11px; "
            "font-family: monospace; border: none;"
        )

        # ── Attempt dots ───────────────────────────────────
        self.lbl_dots = QLabel("")
        self.lbl_dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_dots.setStyleSheet(
            "color: #ff3355; font-size: 14px; border: none;"
        )

        # ── Date and time ──────────────────────────────────
        self.lbl_time = QLabel("")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet(
            "color: #333355; font-size: 11px; "
            "font-family: monospace; border: none;"
        )
        self._update_time_label()
        time_timer = QTimer(self)
        time_timer.timeout.connect(self._update_time_label)
        time_timer.start(1000)

        # ── Assemble card ──────────────────────────────────
        card_layout.addWidget(lbl_os)
        card_layout.addSpacing(8)
        card_layout.addLayout(avatar_row)
        card_layout.addWidget(self.lbl_name)
        card_layout.addWidget(lbl_user)
        card_layout.addSpacing(8)
        card_layout.addLayout(pw_row)
        card_layout.addWidget(self.confirm_input)
        card_layout.addWidget(self.btn_login)
        card_layout.addWidget(self.lbl_status)
        card_layout.addWidget(self.lbl_dots)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.lbl_time)

        self.card.setLayout(card_layout)

        main_layout.addWidget(self.card)
        self.setLayout(main_layout)

        # Focus password field
        QTimer.singleShot(100, self.pw_input.setFocus)

    # ─────────────────────────────────────────────
    #  LOGIC
    # ─────────────────────────────────────────────

    def _on_submit(self):
        """Handles login button or Enter key press."""
        if self._locked:
            return

        password = self.pw_input.text()

        if not password:
            self._set_status("Enter your password.")
            return

        if self._first_run:
            self._handle_first_run(password)
        else:
            self._handle_login(password)

    def _handle_first_run(self, password):
        """
        First run — user is setting a new password.
        Requires confirmation match before saving.
        """
        confirm = self.confirm_input.text()

        if len(password) < 4:
            self._set_status("Password must be at least 4 characters.")
            self._shake()
            return

        if password != confirm:
            self._set_status("Passwords do not match.")
            self.confirm_input.clear()
            self._shake()
            return

        # Save hashed password
        self._session["password_hash"] = _hash_password(password)
        self._session["session_active"] = True
        _save_session(self._session)

        self._set_status("Password set. Welcome to VORTEX OS!", ok=True)
        QTimer.singleShot(800, self._on_success)

    def _handle_login(self, password):
        """
        Normal login — checks password hash against stored hash.
        Tracks failed attempts and locks after max_attempts.
        """
        stored_hash = self._session.get("password_hash", "")
        entered_hash = _hash_password(password)

        if entered_hash == stored_hash:
            # Correct password
            self._session["session_active"] = True
            _save_session(self._session)
            self._set_status("ACCESS GRANTED", ok=True)
            QTimer.singleShot(600, self._on_success)

        else:
            # Wrong password
            self._attempts += 1
            remaining = self._max_attempts - self._attempts

            self.pw_input.clear()
            self._shake()

            # Update attempt dots
            dots = "●" * self._attempts + "○" * remaining
            self.lbl_dots.setText(dots)

            if remaining <= 0:
                self._lockout()
            else:
                self._set_status(
                    f"INCORRECT PASSWORD  —  {remaining} attempt(s) remaining"
                )

    def _lockout(self):
        """
        Locks the login screen for _lock_secs seconds after
        too many failed attempts.
        """
        self._locked       = True
        self._lock_remain  = self._lock_secs
        self.pw_input.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.lbl_dots.setText("●" * self._max_attempts)

        self._lock_timer = QTimer(self)
        self._lock_timer.timeout.connect(self._lockout_tick)
        self._lock_timer.start(1000)

    def _lockout_tick(self):
        """Counts down the lockout timer."""
        self._lock_remain -= 1
        self._set_status(
            f"LOCKED — wait {self._lock_remain}s",
        )
        if self._lock_remain <= 0:
            self._lock_timer.stop()
            self._locked = False
            self._attempts = 0
            self.pw_input.setEnabled(True)
            self.btn_login.setEnabled(True)
            self.lbl_dots.setText("")
            self._set_status("Enter your password.")
            self.pw_input.setFocus()

    def _on_success(self):
        """Hides login screen and emits success signal."""
        self._anim_timer.stop()
        self.hide()
        self.login_successful.emit()

    def _auto_login(self):
        """Skips login when auto_login is enabled in session.json."""
        self._session["session_active"] = True
        _save_session(self._session)
        self._on_success()

    def _set_status(self, message, ok=False):
        """Updates the status label with colored text."""
        if ok:
            self.lbl_status.setStyleSheet(
                "color: #00ff88; font-size: 11px; "
                "font-family: monospace; border: none;"
            )
        else:
            self.lbl_status.setStyleSheet(
                "color: #ff3355; font-size: 11px; "
                "font-family: monospace; border: none;"
            )
        self.lbl_status.setText(message)

    def _toggle_show(self, checked):
        """Toggles password visibility."""
        mode = (QLineEdit.EchoMode.Normal
                if checked else
                QLineEdit.EchoMode.Password)
        self.pw_input.setEchoMode(mode)
        self.confirm_input.setEchoMode(mode)

    def _update_time_label(self):
        """Updates the clock label every second."""
        now = datetime.datetime.now()
        self.lbl_time.setText(
            now.strftime("%A, %d %B %Y  ·  %H:%M:%S").upper()
        )



    def _next_theme_color(self):
     """
    Advances to the next theme color in the slideshow.
    Called every 10 seconds by _slide_timer.
    Starts a smooth 20-step color transition.
     """
     self._theme_idx    = (self._theme_idx + 1) % len(self._theme_colors)
     self._target_color = self._theme_colors[self._theme_idx]
     self._transition_step = 0
     self._in_transition   = True

    # Start transition timer at ~30fps
     self._trans_timer.start(33)

    def _transition_tick(self):
     """
    Called every 33ms during a color transition.
    Interpolates _current_color toward _target_color over 20 steps.

    Color interpolation:
    We parse both hex colors into R,G,B, then lerp each channel
    separately. At step 20 we snap to the exact target.
    """
     self._transition_step += 1
     total_steps = 20

    # Parse current and target into RGB
     def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

     def rgb_to_hex(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"

     cr, cg, cb = hex_to_rgb(self._current_color)
     tr, tg, tb = hex_to_rgb(self._target_color)

     t = self._transition_step / total_steps   # 0.0 → 1.0

    # Linear interpolation for each channel
     nr = int(cr + (tr - cr) * t)
     ng = int(cg + (tg - cg) * t)
     nb = int(cb + (tb - cb) * t)

     self._current_color = rgb_to_hex(nr, ng, nb)

    # Update card border and OS label to match new color
     self._update_card_color(self._current_color)

    # Repaint background
     self.update()

    # Stop when transition complete
     if self._transition_step >= total_steps:
        self._trans_timer.stop()
        self._current_color = self._target_color
        self._in_transition  = False
        self._update_card_color(self._current_color)

    def _update_card_color(self, hex_color):
     """
    Updates the card border, login button, and OS label
    to match the current slideshow color.
    """
    # Card border
     self.card.setStyleSheet(f"""
        QWidget {{
            background-color: rgba(10, 10, 20, 220);
            border: 1px solid {hex_color};
            border-radius: 8px;
        }}
    """)

    # OS label at top of card
    # Find it by iterating card's children
     for child in self.card.findChildren(QLabel):
        if child.text() == "VORTEX OS":
            child.setStyleSheet(
                f"color: {hex_color}; font-size: 13px; "
                f"font-weight: bold; letter-spacing: 6px; border: none;"
            )
            break

    # Login button border
     self.btn_login.setStyleSheet(f"""
        QPushButton {{
            background-color: #001a1a;
            color: {hex_color};
            border: 1px solid {hex_color};
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 3px;
        }}
        QPushButton:hover {{
            background-color: #003333;
            border-color: white;
        }}
    """)

    # Password input focus border
     self.pw_input.setStyleSheet(f"""
        QLineEdit {{
            background-color: #0a0a14;
            color: {hex_color};
            border: 1px solid #003333;
            border-radius: 4px;
            padding: 8px 12px;
            font-family: monospace;
            font-size: 14px;
            letter-spacing: 3px;
        }}
        QLineEdit:focus {{
            border-color: {hex_color};
        }}
    """)

    # ─────────────────────────────────────────────
    #  SHAKE ANIMATION
    # ─────────────────────────────────────────────

    def _shake(self):
        """
        Shakes the login card horizontally.
        Classic wrong-password feedback used in all major OSes.

        Uses QPropertyAnimation on the card's position.
        The card moves left and right rapidly then returns to center.
        """
        original_x = self.card.pos().x()
        original_y = self.card.pos().y()

        self._shake_anim = QPropertyAnimation(self.card, b"pos")
        self._shake_anim.setDuration(400)
        self._shake_anim.setEasingCurve(QEasingCurve.Type.Linear)

        # Keyframes: right → left → right → left → center
        self._shake_anim.setKeyValueAt(0.0,  QPoint(original_x,      original_y))
        self._shake_anim.setKeyValueAt(0.15, QPoint(original_x + 18, original_y))
        self._shake_anim.setKeyValueAt(0.30, QPoint(original_x - 18, original_y))
        self._shake_anim.setKeyValueAt(0.45, QPoint(original_x + 12, original_y))
        self._shake_anim.setKeyValueAt(0.60, QPoint(original_x - 12, original_y))
        self._shake_anim.setKeyValueAt(0.75, QPoint(original_x + 6,  original_y))
        self._shake_anim.setKeyValueAt(0.90, QPoint(original_x - 6,  original_y))
        self._shake_anim.setKeyValueAt(1.0,  QPoint(original_x,      original_y))

        self._shake_anim.start()

    # ─────────────────────────────────────────────
    #  BACKGROUND PAINTING
    # ─────────────────────────────────────────────

    def _tick_bg(self):
        self._tick += 1
        self.update()

    def paintEvent(self, event):
     import math
     painter = QPainter(self)
     painter.setRenderHint(QPainter.RenderHint.Antialiasing)

     w = self.width()
     h = self.height()

     painter.fillRect(0, 0, w, h, QColor("#030308"))

    # Parse current slideshow color into RGB
     def hex_to_rgb(hx):
        hx = hx.lstrip('#')
        return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))

     cr, cg, cb = hex_to_rgb(self._current_color)

    # Dot grid using current theme color
     spacing = 36
     cols    = w // spacing + 2
     rows    = h // spacing + 2

     for row in range(rows):
        for col in range(cols):
            x          = col * spacing
            y          = row * spacing
            phase      = (col + row) * 0.4 + self._tick * 0.02
            brightness = (math.sin(phase) + 1.0) / 2.0
            intensity  = brightness * 0.08   # 0.0 – 0.08 multiplier

            dot_r = int(cr * intensity)
            dot_g = int(cg * intensity)
            dot_b = int(cb * intensity)
            color = QColor(dot_r, dot_g, dot_b)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))

            from PyQt6.QtCore import QPointF
            painter.drawEllipse(QPointF(x, y), 1.0, 1.0)

    # Vignette
     grad = QLinearGradient(0, 0, 0, h)
     grad.setColorAt(0.0, QColor(0, 0, 0, 120))
     grad.setColorAt(0.4, QColor(0, 0, 0, 0))
     grad.setColorAt(0.6, QColor(0, 0, 0, 0))
     grad.setColorAt(1.0, QColor(0, 0, 0, 120))
     painter.fillRect(0, 0, w, h, grad)