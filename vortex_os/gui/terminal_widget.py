# gui/terminal_widget.py
# VORTEX OS - Embedded GUI Terminal Widget
# A terminal emulator running inside the PyQt6 desktop.

import json
import datetime
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QLabel, QPushButton,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui  import QTextCursor, QColor, QTextCharFormat, QFont

from gui.styles import (
    TERMINAL_CONTAINER, TERMINAL_TITLEBAR,
    TERMINAL_TITLE_LABEL, TERMINAL_OUTPUT,
    TERMINAL_INPUT, TERMINAL_CLOSE_BTN
)


# ── ANSI color → Qt color mapping ─────────────────────────
# The terminal commands use colorama ANSI codes.
# We strip them and apply Qt colors instead for GUI rendering.

ANSI_COLORS = {
    "36":  "#00ffff",    # Cyan       → PRIMARY
    "32":  "#00ff88",    # Green      → SUCCESS
    "33":  "#ffcc00",    # Yellow     → WARNING
    "31":  "#ff3355",    # Red        → ERROR
    "35":  "#cc00ff",    # Magenta    → ACCENT
    "37":  "#e0e0ff",    # White      → TEXT
    "90":  "#444466",    # Dark grey  → DIM
    "1":   None,         # Bold (handled separately)
    "0":   None,         # Reset
}


class CommandWorker(QObject):
    """
    Runs a single VORTEX command in a worker thread.
    Captures stdout output and sends it back via signal.

    Why a worker thread?
    Commands like 'scan' or 'vault find' can take a second or two.
    Running them on the main thread would freeze the GUI.
    The worker runs them off-thread, sending output back safely.
    """

    output_ready  = pyqtSignal(str)
    command_done  = pyqtSignal()

    def __init__(self, command_text, config, router):
        super().__init__()
        self.command_text = command_text
        self.config       = config
        self.router       = router

    def run(self):
        """Executes the command, captures print output."""
        import io
        import sys

        # Redirect stdout to capture print() calls from commands
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured

        try:
            from terminal.parser import CommandParser
            parser  = CommandParser()
            parsed  = parser.parse(self.command_text)
            if parsed:
                self.router.execute(parsed, self.config)
        except Exception as e:
            print(f"  [ERROR] {e}")
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        if output.strip():
            self.output_ready.emit(output)
        self.command_done.emit()


class EmbeddedTerminal(QWidget):
    """
    A full VORTEX terminal running inside the desktop GUI.

    Components:
    - Title bar (draggable, with close button)
    - Output area (QTextEdit, read-only, colored)
    - Input line (QLineEdit with history)

    The terminal uses the same CommandParser + CommandRouter
    as the console terminal — identical command set.
    """

    # Emitted when the user closes this terminal window
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalContainer")
        self.setStyleSheet(TERMINAL_CONTAINER)
        self.setMinimumSize(500, 350)

        # Load config and set up router
        self._config  = self._load_config()
        self._router  = self._build_router()
        self._history = []
        self._hist_idx = -1

        # Thread reference (kept alive while command runs)
        self._worker_thread = None

        self._build_ui()
        self._print_banner()

    def _load_config(self):
        try:
            with open("config/settings.json", "r") as f:
                return json.load(f)
        except Exception:
            return {
                "os_name":  "VORTEX OS",
                "version":  "0.1.0",
                "codename": "GENESIS",
            }

    def _build_router(self):
        """Creates a CommandRouter with all commands registered."""
        from terminal.router import CommandRouter
        from commands.builtin_commands import (
            cmd_help, cmd_clock, cmd_clear,
            cmd_system, cmd_exit, cmd_version, cmd_whoami
        )
        from commands.system_commands import (
            cmd_vault, cmd_scan, cmd_apps, cmd_ignite, cmd_open
        )
        from commands.theme_commands import cmd_theme, cmd_history

        router = CommandRouter()
        router.register_many({
            "help":     (cmd_help,    "Show commands"),
            "clock":    (cmd_clock,   "Show time"),
            "clear":    (cmd_clear,   "Clear terminal"),
            "system":   (cmd_system,  "System info"),
            "version":  (cmd_version, "OS version"),
            "whoami":   (cmd_whoami,  "User identity"),
            "vault":    (cmd_vault,   "File explorer"),
            "scan":     (cmd_scan,    "System scanner"),
            "apps":     (cmd_apps,    "App registry"),
            "theme":    (cmd_theme,   "Theme switcher"),
            "history":  (cmd_history, "Command history"),
            "exit":     (cmd_exit,    "Exit"),
        })

        self._config["_router"] = router
        return router

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Title bar ──────────────────────────────
        titlebar = QWidget()
        titlebar.setObjectName("TerminalTitlebar")
        titlebar.setFixedHeight(28)
        titlebar.setStyleSheet(TERMINAL_TITLEBAR)

        tb_layout = QHBoxLayout()
        tb_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel("▶ VORTEX TERMINAL")
        self.lbl_title.setStyleSheet(TERMINAL_TITLE_LABEL)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(TERMINAL_CLOSE_BTN)
        btn_close.clicked.connect(self._on_close)

        tb_layout.addWidget(self.lbl_title)
        tb_layout.addStretch()
        btn_close.setParent(titlebar)
        tb_layout.addWidget(btn_close)
        titlebar.setLayout(tb_layout)

        # ── Output area ────────────────────────────
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(TERMINAL_OUTPUT)
        self.output.setFont(QFont("monospace", 11))
        self.output.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # ── Input row ──────────────────────────────
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(0)

        self.prompt_label = QLabel("[VORTEX] > ")
        self.prompt_label.setStyleSheet(
            "QLabel { color: #00ffff; font-family: monospace; "
            "font-size: 12px; padding: 6px 4px 6px 8px; "
            "background-color: #0d0d1a; border-top: 1px solid #003333; }"
        )

        self.input_line = QLineEdit()
        self.input_line.setStyleSheet(TERMINAL_INPUT)
        self.input_line.returnPressed.connect(self._on_submit)
        self.input_line.installEventFilter(self)

        input_row.addWidget(self.prompt_label)
        input_row.addWidget(self.input_line)

        # ── Assemble ───────────────────────────────
        layout.addWidget(titlebar)
        layout.addWidget(self.output)
        layout.addLayout(input_row)

        self.setLayout(layout)

    def _print_banner(self):
        """Prints the welcome message into the output area."""
        banner_lines = [
            ("◈ VORTEX TERMINAL  v0.1.0  [GENESIS]", "#00ffff"),
            ("Type 'help' for available commands.", "#444466"),
            ("", None),
        ]
        for text, color in banner_lines:
            self._append_colored(text, color or "#444466")

    def _append_colored(self, text, color="#e0e0ff"):
        """Appends a line of colored text to the output area."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")

        # Auto-scroll to bottom
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _append_output(self, raw_text):
        """
        Takes raw terminal output (with ANSI codes) and renders
        it in the GUI output area with appropriate colors.

        We use a simple ANSI parser — not a full VT100 emulator.
        We only handle the color codes that VORTEX commands emit.
        """
        import re

        # Split on ANSI escape sequences
        # Pattern matches ESC[ ... m  (color codes)
        ansi_escape = re.compile(r'\x1b\[([0-9;]+)m')
        current_color = "#e0e0ff"

        parts = ansi_escape.split(raw_text)

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        i = 0
        while i < len(parts):
            part = parts[i]

            # Even indices are text, odd are ANSI codes
            if i % 2 == 0:
                if part:
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor(current_color))
                    cursor.setCharFormat(fmt)
                    cursor.insertText(part)
            else:
                # Parse color code
                codes = part.split(";")
                for code in codes:
                    if code in ANSI_COLORS and ANSI_COLORS[code]:
                        current_color = ANSI_COLORS[code]
                    elif code == "0" or code == "":
                        current_color = "#e0e0ff"
            i += 1

        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _on_submit(self):
        """Called when user presses Enter in the input field."""
        text = self.input_line.text().strip()
        if not text:
            return

        # Show command in output with prompt prefix
        self._append_colored(f"[VORTEX] > {text}", "#00ffff")

        # Add to history
        self._history.append(text)
        self._hist_idx = len(self._history)

        # Clear input
        self.input_line.clear()

        # Handle clear specially (clears the QTextEdit)
        if text.strip() == "clear":
            self.output.clear()
            return

        # Handle exit
        if text.strip() in ("exit", "quit", "q"):
            self._append_colored("  Session ended.", "#444466")
            return

        # Run command in worker thread
        self._run_command(text)

    def _run_command(self, text):
        """Runs a command off the main thread to keep GUI responsive."""
        self.input_line.setEnabled(False)
        self.lbl_title.setText("▶ VORTEX TERMINAL  [running...]")

        # Create worker and thread
        self._worker_thread = QThread()
        self._worker = CommandWorker(text, self._config, self._router)
        self._worker.moveToThread(self._worker_thread)

        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker.output_ready.connect(self._append_output)
        self._worker.command_done.connect(self._on_command_done)
        self._worker.command_done.connect(self._worker_thread.quit)

        self._worker_thread.start()

    def _on_command_done(self):
        """Called when command finishes — re-enable input."""
        self.input_line.setEnabled(True)
        self.input_line.setFocus()
        self.lbl_title.setText("▶ VORTEX TERMINAL")

    def eventFilter(self, obj, event):
        """Intercepts key events on the input line for history navigation."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui  import QKeyEvent

        if obj is self.input_line and event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if key == Qt.Key.Key_Up:
                # Navigate back in history
                if self._history and self._hist_idx > 0:
                    self._hist_idx -= 1
                    self.input_line.setText(self._history[self._hist_idx])
                return True

            if key == Qt.Key.Key_Down:
                # Navigate forward in history
                if self._hist_idx < len(self._history) - 1:
                    self._hist_idx += 1
                    self.input_line.setText(self._history[self._hist_idx])
                else:
                    self._hist_idx = len(self._history)
                    self.input_line.clear()
                return True

        return super().eventFilter(obj, event)

    def _on_close(self):
        """Hides the terminal and emits closed signal."""
        self.hide()
        self.closed.emit()