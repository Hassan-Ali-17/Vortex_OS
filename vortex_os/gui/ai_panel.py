# gui/ai_panel.py
# VORTEX OS - ARIA AI Assistant Panel
# Slides in from the right side of the desktop.

import json
import os
import threading
import urllib.request
import urllib.error

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QLineEdit, QScrollArea, QSizePolicy
)
from PyQt6.QtCore    import (
    Qt, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QObject, QTimer
)
from PyQt6.QtGui     import QFont, QColor, QTextCursor


AI_CONFIG_PATH = "config/ai_config.json"

PANEL_STYLE = """
    QWidget#AIPanel {
        background-color: #08080f;
        border-left: 1px solid #1a0a2e;
    }
"""

HEADER_STYLE = """
    QWidget {
        background-color: #0d0a1a;
        border-bottom: 1px solid #1a0a2e;
    }
"""

OUTPUT_STYLE = """
    QTextEdit {
        background-color: #07070e;
        color: #e0e0ff;
        font-family: monospace;
        font-size: 12px;
        border: none;
        padding: 10px;
        selection-background-color: #1a0a2e;
    }
"""

INPUT_STYLE = """
    QLineEdit {
        background-color: #0d0a1a;
        color: #cc00ff;
        font-family: monospace;
        font-size: 12px;
        border: none;
        border-top: 1px solid #1a0a2e;
        padding: 8px 10px;
    }
    QLineEdit:focus {
        border-top-color: #cc00ff;
    }
"""


class _APIWorker(QObject):
    """
    Calls the Anthropic API in a background thread.
    Emits response_chunk for each streamed token
    and response_done when complete.

    Why a separate QObject worker?
    API calls can take 2-10 seconds. Running on the main thread
    would freeze the entire GUI. We run it in a Python thread
    and communicate back via Qt signals.
    """

    response_chunk = pyqtSignal(str)
    response_done  = pyqtSignal()
    response_error = pyqtSignal(str)

    def __init__(self, messages, config):
        super().__init__()
        self.messages = messages
        self.config   = config

    def run(self):
        """Calls the API and emits chunks as they arrive."""
        api_key = os.environ.get(
            self.config.get("api_key_env", "ANTHROPIC_API_KEY"), ""
        )

        if not api_key:
            self.response_error.emit(
                "ANTHROPIC_API_KEY not set.\n"
                "Run: export ANTHROPIC_API_KEY=your_key_here"
            )
            return

        payload = {
            "model":      self.config.get("model",
                          "claude-sonnet-4-20250514"),
            "max_tokens": self.config.get("max_tokens", 1024),
            "system":     self.config.get("system_prompt", ""),
            "messages":   self.messages,
            "stream":     True,
        }

        headers = {
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            req  = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data    = json.dumps(payload).encode(),
                headers = headers,
                method  = "POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()

                    if not line.startswith("data:"):
                        continue

                    data_str = line[5:].strip()

                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Extract text delta from stream
                    if data.get("type") == "content_block_delta":
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                self.response_chunk.emit(text)

        except urllib.error.HTTPError as e:
            body = e.read().decode()
            self.response_error.emit(f"API Error {e.code}: {body[:200]}")
        except urllib.error.URLError as e:
            self.response_error.emit(f"Network error: {e.reason}")
        except Exception as e:
            self.response_error.emit(f"Error: {str(e)}")
        finally:
            self.response_done.emit()


class AIPanelWidget(QWidget):
    """
    The ARIA AI assistant panel.
    Slides in from the right edge of the desktop.

    Features:
    - Full conversation history within a session
    - Streamed responses (text appears as it generates)
    - Thinking indicator while waiting for API
    - Clear conversation button
    - Keyboard: Enter sends, Shift+Enter newline
    """

    WIDTH = 380

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AIPanel")
        self.setFixedWidth(self.WIDTH)
        self.setStyleSheet(PANEL_STYLE)

        self._config       = self._load_config()
        self._history      = []   # List of {role, content} dicts
        self._is_thinking  = False
        self._visible      = False
        self._think_dots   = 0

        self._build_ui()

        # Thinking animation timer
        self._think_timer = QTimer(self)
        self._think_timer.timeout.connect(self._tick_thinking)

        if parent:
            self.resize(self.WIDTH, parent.height())
            # Start hidden off right edge
            self.move(parent.width(), 0)

    def _load_config(self):
        try:
            with open(AI_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system_prompt": "You are ARIA, the VORTEX OS AI assistant.",
                "api_key_env": "ANTHROPIC_API_KEY",
                "history_limit": 20,
            }

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ─────────────────────────────────
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(HEADER_STYLE)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 8, 0)

        lbl_title = QLabel("◈ ARIA  —  AI ASSISTANT")
        lbl_title.setStyleSheet(
            "color: #cc00ff; font-size: 11px; font-weight: bold;"
            "letter-spacing: 3px;"
        )

        btn_clear = QPushButton("✕ CLEAR")
        btn_clear.setFixedSize(70, 28)
        btn_clear.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #333355;
                border: 1px solid #1a1a2e;
                font-size: 10px;
                font-family: monospace;
                padding: 2px;
            }
            QPushButton:hover {
                color: #cc00ff;
                border-color: #cc00ff;
            }
        """)
        btn_clear.clicked.connect(self._clear_conversation)

        h_layout.addWidget(lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(btn_clear)
        header.setLayout(h_layout)

        # ── Output area ────────────────────────────
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUTPUT_STYLE)
        self.output.setFont(QFont("monospace", 11))

        # ── Thinking indicator ─────────────────────
        self.lbl_thinking = QLabel("")
        self.lbl_thinking.setFixedHeight(20)
        self.lbl_thinking.setStyleSheet(
            "color: #440066; font-size: 10px; "
            "font-family: monospace; padding-left: 10px;"
            "background: #07070e;"
        )

        # ── Input row ──────────────────────────────
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(0)

        self.prompt_lbl = QLabel("ARIA > ")
        self.prompt_lbl.setStyleSheet(
            "color: #cc00ff; font-family: monospace; font-size: 12px;"
            "padding: 8px 4px 8px 10px; background: #0d0a1a;"
            "border-top: 1px solid #1a0a2e;"
        )

        self.input_line = QLineEdit()
        self.input_line.setStyleSheet(INPUT_STYLE)
        self.input_line.setPlaceholderText("Ask ARIA anything...")
        self.input_line.returnPressed.connect(self._on_submit)

        input_row.addWidget(self.prompt_lbl)
        input_row.addWidget(self.input_line)

        # ── API key hint ───────────────────────────
        self.lbl_hint = QLabel(
            "Set ANTHROPIC_API_KEY to activate"
        )
        self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_hint.setFixedHeight(20)
        self.lbl_hint.setStyleSheet(
            "color: #220033; font-size: 9px; "
            "font-family: monospace; background: #07070e;"
        )

        # Show hint only if key not set
        api_key = os.environ.get(
            self._config.get("api_key_env", "ANTHROPIC_API_KEY"), ""
        )
        self.lbl_hint.setVisible(not bool(api_key))

        # ── Assemble ───────────────────────────────
        layout.addWidget(header)
        layout.addWidget(self.output, 1)
        layout.addWidget(self.lbl_thinking)
        layout.addWidget(self.lbl_hint)
        layout.addLayout(input_row)

        self.setLayout(layout)
        self._print_welcome()

    def _print_welcome(self):
        """Prints the welcome message."""
        self._append("ARIA", (
            "ARIA online. VORTEX OS AI assistant ready.\n\n"
            "Ask me anything — commands, Linux, code, "
            "or general questions.\n\n"
            "Type 'help' to see what VORTEX commands are available."
        ), "#cc00ff")

    # ─────────────────────────────────────────────
    #  CONVERSATION
    # ─────────────────────────────────────────────

    def _on_submit(self):
        """Handles user pressing Enter in the input field."""
        text = self.input_line.text().strip()
        if not text or self._is_thinking:
            return

        self.input_line.clear()

        # Show user message
        self._append("YOU", text, "#00ffff")

        # Add to history
        self._history.append({"role": "user", "content": text})

        # Trim history to limit
        limit = self._config.get("history_limit", 20)
        if len(self._history) > limit:
            self._history = self._history[-limit:]

        # Check for local commands first
        if self._handle_local(text):
            return

        # Send to API
        self._send_to_api()

    def _handle_local(self, text):
        """
        Handles commands that don't need the API.
        Returns True if handled locally, False if should go to API.
        """
        lower = text.lower().strip()

        if lower in ("help", "commands", "what can you do"):
            self._append("ARIA", (
                "I can help you with:\n\n"
                "• VORTEX commands — 'how do I list files?'\n"
                "• Linux questions — 'what does chmod do?'\n"
                "• Python help — 'explain decorators'\n"
                "• Error debugging — paste an error message\n"
                "• General Q&A — anything you want to know\n\n"
                "VORTEX commands: vault, vx, scan, theme, "
                "app, landmark, clock, system, whoami..."
            ), "#cc00ff")
            return True

        if lower == "clear":
            self._clear_conversation()
            return True

        return False

    def _send_to_api(self):
        """Starts the API call in a background thread."""
        self._is_thinking = True
        self._think_dots  = 0
        self._think_timer.start(400)
        self.input_line.setEnabled(False)

        # Create worker
        worker = _APIWorker(
            messages = list(self._history),
            config   = self._config
        )
        worker.response_chunk.connect(self._on_chunk)
        worker.response_done.connect(self._on_done)
        worker.response_error.connect(self._on_error)

        # Keep reference
        self._worker = worker

        # Start in Python thread (not QThread — simpler for this use)
        self._api_thread = threading.Thread(
            target=worker.run, daemon=True
        )

        # Prepare output area for streamed response
        self._append_start("ARIA", "#cc00ff")
        self._response_buffer = ""

        self._api_thread.start()

    def _on_chunk(self, text):
        """Called for each streamed token — appends to output."""
        self._response_buffer += text
        self._append_inline(text)

    def _on_done(self):
        """Called when API response is complete."""
        self._is_thinking = False
        self._think_timer.stop()
        self.lbl_thinking.setText("")
        self.input_line.setEnabled(True)
        self.input_line.setFocus()

        # Add assistant response to history
        if self._response_buffer:
            self._history.append({
                "role":    "assistant",
                "content": self._response_buffer
            })
            self._response_buffer = ""

        # Add spacing after response
        self._append_newline()

    def _on_error(self, error_msg):
        """Called if API call fails."""
        self._is_thinking = False
        self._think_timer.stop()
        self.lbl_thinking.setText("")
        self.input_line.setEnabled(True)
        self.input_line.setFocus()
        self._append("ERROR", error_msg, "#ff3355")

    def _tick_thinking(self):
        """Animates the thinking indicator dots."""
        self._think_dots = (self._think_dots + 1) % 4
        dots = "·" * self._think_dots
        self.lbl_thinking.setText(f"  ARIA thinking{dots}")

    def _clear_conversation(self):
        """Clears history and output."""
        self._history = []
        self.output.clear()
        self._print_welcome()

    # ─────────────────────────────────────────────
    #  OUTPUT HELPERS
    # ─────────────────────────────────────────────

    def _append(self, speaker, text, color):
        """Appends a complete message block to the output."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        from PyQt6.QtGui import QTextCharFormat
        fmt = QTextCharFormat()

        # Speaker label
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(QFont.Weight.Bold)
        cursor.setCharFormat(fmt)
        cursor.insertText(f"\n{speaker}\n")

        # Body text
        fmt.setForeground(QColor("#aaaacc"))
        fmt.setFontWeight(QFont.Weight.Normal)
        cursor.setCharFormat(fmt)
        cursor.insertText(f"{text}\n")

        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _append_start(self, speaker, color):
        """Starts a new message block (for streaming)."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        from PyQt6.QtGui import QTextCharFormat
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        fmt.setFontWeight(QFont.Weight.Bold)
        cursor.setCharFormat(fmt)
        cursor.insertText(f"\n{speaker}\n")

        fmt.setForeground(QColor("#aaaacc"))
        fmt.setFontWeight(QFont.Weight.Normal)
        cursor.setCharFormat(fmt)

        self.output.setTextCursor(cursor)

    def _append_inline(self, text):
        """Appends text inline (used during streaming)."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        from PyQt6.QtGui import QTextCharFormat
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#aaaacc"))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)

        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _append_newline(self):
        """Appends a blank line after a response."""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n")
        self.output.setTextCursor(cursor)

    # ─────────────────────────────────────────────
    #  SLIDE ANIMATION
    # ─────────────────────────────────────────────

    def toggle(self):
        """Slides the panel in or out."""
        if self._visible:
            self._slide_out()
        else:
            self._slide_in()

    def _slide_in(self):
        """Slides panel in from the right."""
        if self.parent():
            self.resize(self.WIDTH, self.parent().height())
            target_x = self.parent().width() - self.WIDTH
        else:
            target_x = 800

        self.show()
        self.raise_()

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(280)
        anim.setStartValue(self.pos())
        anim.setEndValue(self.pos().__class__(target_x, 0))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim    = anim
        self._visible = True

        QTimer.singleShot(300, self.input_line.setFocus)

    def _slide_out(self):
        """Slides panel out to the right."""
        if self.parent():
            off_x = self.parent().width()
        else:
            off_x = 1920

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(220)
        anim.setStartValue(self.pos())
        anim.setEndValue(self.pos().__class__(off_x, 0))
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.hide)
        anim.start()
        self._anim    = anim
        self._visible = False