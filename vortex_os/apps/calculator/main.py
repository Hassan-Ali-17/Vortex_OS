# apps/calculator/main.py
# VORTEX OS - Calculator App

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont
from apps.base_app import BaseApp


class CalculatorApp(BaseApp):
    """
    A cyberpunk-styled calculator.

    Supports:
    - Basic arithmetic: + - * /
    - Percentage: %
    - Sign toggle: +/-
    - Decimal point
    - Keyboard input (numbers + operators)
    - Clear (C) and backspace (⌫)
    - Expression display showing full calculation
    """

    def get_title(self):
        return "◈ VORTEX CALC"

    def setup_ui(self):
        self.setFixedSize(320, 480)

        self._expression = ""   # What we're building
        self._result     = ""   # Last computed result
        self._just_evaluated = False

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Header ─────────────────────────────────
        header = QLabel("◈ VORTEX CALC")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "color: #00ffff; font-size: 11px; "
            "font-weight: bold; letter-spacing: 3px;"
        )

        # ── Expression display (small, top) ────────
        self.lbl_expr = QLabel("")
        self.lbl_expr.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_expr.setFixedHeight(24)
        self.lbl_expr.setStyleSheet(
            "color: #444466; font-size: 12px; "
            "font-family: monospace;"
        )

        # ── Main display ───────────────────────────
        self.lbl_display = QLabel("0")
        self.lbl_display.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_display.setFixedHeight(72)
        self.lbl_display.setStyleSheet(
            "color: #00ffff; font-size: 36px; "
            "font-weight: bold; font-family: monospace; "
            "background: #0a0a14; padding: 8px; "
            "border: 1px solid #003333;"
        )

        # ── Button grid ────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(6)

        # Button layout:
        # Row 0: C   +/-  %    ÷
        # Row 1: 7   8    9    ×
        # Row 2: 4   5    6    −
        # Row 3: 1   2    3    +
        # Row 4: 0(wide)  .    =

        buttons = [
            # (label, row, col, colspan, style)
            ("C",   0, 0, 1, "func"),
            ("+/-", 0, 1, 1, "func"),
            ("%",   0, 2, 1, "func"),
            ("÷",   0, 3, 1, "op"),
            ("7",   1, 0, 1, "num"),
            ("8",   1, 1, 1, "num"),
            ("9",   1, 2, 1, "num"),
            ("×",   1, 3, 1, "op"),
            ("4",   2, 0, 1, "num"),
            ("5",   2, 1, 1, "num"),
            ("6",   2, 2, 1, "num"),
            ("−",   2, 3, 1, "op"),
            ("1",   3, 0, 1, "num"),
            ("2",   3, 1, 1, "num"),
            ("3",   3, 2, 1, "num"),
            ("+",   3, 3, 1, "op"),
            ("0",   4, 0, 2, "num"),
            (".",   4, 2, 1, "num"),
            ("=",   4, 3, 1, "eq"),
        ]

        styles = {
            "num":  ("background:#0d0d1a; color:#e0e0ff; "
                     "border:1px solid #1a1a2e; font-size:18px;"),
            "op":   ("background:#0a1a2a; color:#00ffff; "
                     "border:1px solid #003355; font-size:18px;"),
            "func": ("background:#0d0d1a; color:#888899; "
                     "border:1px solid #1a1a2e; font-size:16px;"),
            "eq":   ("background:#003333; color:#00ffff; "
                     "border:1px solid #006666; font-size:18px; "
                     "font-weight:bold;"),
        }

        hover_extra = (
            "QPushButton:hover { background:#1a1a2e; "
            "border-color:#00ffff; color:#00ffff; }"
            "QPushButton:pressed { background:#003333; }"
        )

        for label, row, col, span, kind in buttons:
            btn = QPushButton(label)
            btn.setFixedHeight(56)
            btn.setFont(QFont("monospace", 14))
            base_style = styles[kind]
            btn.setStyleSheet(
                f"QPushButton {{ {base_style} }}" + hover_extra
            )
            btn.clicked.connect(
                lambda checked=False, l=label: self._on_button(l)
            )
            grid.addWidget(btn, row, col, 1, span)

        layout.addWidget(header)
        layout.addWidget(self.lbl_expr)
        layout.addWidget(self.lbl_display)
        layout.addLayout(grid)
        self.setLayout(layout)

    def _on_button(self, label):
        """Handles button press logic."""
        if label == "C":
            self._expression       = ""
            self._result           = ""
            self._just_evaluated   = False
            self.lbl_display.setText("0")
            self.lbl_expr.setText("")
            return

        if label == "+/-":
            current = self.lbl_display.text()
            try:
                val = float(current)
                val = -val
                display = (str(int(val))
                           if val == int(val) else str(val))
                self.lbl_display.setText(display)
            except ValueError:
                pass
            return

        if label == "%":
            current = self.lbl_display.text()
            try:
                val = float(current) / 100
                display = (str(int(val))
                           if val == int(val) else str(val))
                self.lbl_display.setText(display)
            except ValueError:
                pass
            return

        if label == "=":
            self._evaluate()
            return

        # Operator or number/decimal
        op_map = {"÷": "/", "×": "*", "−": "-", "+": "+"}

        if label in op_map:
            # Append current display value + operator to expression
            if self._just_evaluated:
                self._expression = self.lbl_display.text()
                self._just_evaluated = False
            else:
                self._expression += self.lbl_display.text()
            self._expression += op_map[label]
            self.lbl_expr.setText(
                self._expression.replace("/","÷").replace("*","×")
            )
            self.lbl_display.setText("0")
        else:
            # Number or decimal
            current = self.lbl_display.text()
            if self._just_evaluated:
                current = "0"
                self._expression       = ""
                self._just_evaluated   = False

            if label == "." and "." in current:
                return
            if current == "0" and label != ".":
                self.lbl_display.setText(label)
            else:
                self.lbl_display.setText(current + label)

    def _evaluate(self):
        """Evaluates the full expression."""
        full = self._expression + self.lbl_display.text()
        self.lbl_expr.setText(
            full.replace("/","÷").replace("*","×") + " ="
        )
        try:
            result = eval(full)   # Safe here — user input only
            if isinstance(result, float) and result == int(result):
                result = int(result)
            self.lbl_display.setText(str(result))
            self._expression     = ""
            self._just_evaluated = True
        except Exception:
            self.lbl_display.setText("ERROR")
            self._expression = ""

    def keyPressEvent(self, event):
        """Maps keyboard keys to calculator buttons."""
        key_map = {
            Qt.Key.Key_0: "0", Qt.Key.Key_1: "1",
            Qt.Key.Key_2: "2", Qt.Key.Key_3: "3",
            Qt.Key.Key_4: "4", Qt.Key.Key_5: "5",
            Qt.Key.Key_6: "6", Qt.Key.Key_7: "7",
            Qt.Key.Key_8: "8", Qt.Key.Key_9: "9",
            Qt.Key.Key_Plus:     "+",
            Qt.Key.Key_Minus:    "−",
            Qt.Key.Key_Asterisk: "×",
            Qt.Key.Key_Slash:    "÷",
            Qt.Key.Key_Period:   ".",
            Qt.Key.Key_Return:   "=",
            Qt.Key.Key_Enter:    "=",
            Qt.Key.Key_Escape:   "C",
        }
        label = key_map.get(event.key())
        if label:
            self._on_button(label)


def create_app(manifest):
    """Required entry point. Called by AppRegistry.launch()."""
    return CalculatorApp(manifest)