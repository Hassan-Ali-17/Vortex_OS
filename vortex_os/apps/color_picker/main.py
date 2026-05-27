# apps/color_picker/main.py
# VORTEX OS - Color Picker App

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QLineEdit,
    QApplication, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QColor, QPainter, QBrush

from apps.base_app import BaseApp


class ColorPreview(QWidget):
    """A square that fills with the selected color."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor("#00ffff")
        self.setFixedSize(120, 120)

    def set_color(self, color):
        self._color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(0, 0, self.width(), self.height(), self._color)
        # Checkerboard hint at border
        p.setPen(QColor("#333355"))
        p.drawRect(0, 0, self.width()-1, self.height()-1)


class ColorPickerApp(BaseApp):
    """
    RGB color picker with hex output.

    Three sliders (R, G, B) control a live preview square.
    Copy button copies the hex code to clipboard.
    """

    def get_title(self):
        return "◉ VORTEX COLORS"

    def setup_ui(self):
        self.setFixedSize(340, 380)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        lbl_h = QLabel("◉ COLOR PICKER")
        lbl_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_h.setStyleSheet(
            "color:#cc00ff;font-size:11px;"
            "font-weight:bold;letter-spacing:3px;"
        )

        # Preview + hex row
        preview_row = QHBoxLayout()
        preview_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview = ColorPreview()

        hex_col = QVBoxLayout()
        hex_col.setSpacing(6)

        self.lbl_hex = QLabel("#00FFFF")
        self.lbl_hex.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_hex.setStyleSheet(
            "color:#00ffff;font-size:22px;"
            "font-weight:bold;font-family:monospace;"
        )

        self.lbl_rgb = QLabel("R:0  G:255  B:255")
        self.lbl_rgb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_rgb.setStyleSheet(
            "color:#444466;font-size:10px;font-family:monospace;"
        )

        btn_copy = QPushButton("⎘ COPY HEX")
        btn_copy.setStyleSheet(
            "QPushButton{background:#0a0a14;color:#cc00ff;"
            "border:1px solid #660088;font-size:11px;padding:6px;}"
            "QPushButton:hover{background:#1a0a2e;"
            "border-color:#cc00ff;color:#ffffff;}"
        )
        btn_copy.clicked.connect(self._copy_hex)

        btn_copy_rgb = QPushButton("⎘ COPY RGB")
        btn_copy_rgb.setStyleSheet(
            "QPushButton{background:#0a0a14;color:#444466;"
            "border:1px solid #1a1a2e;font-size:11px;padding:6px;}"
            "QPushButton:hover{background:#111122;"
            "border-color:#888899;color:#e0e0ff;}"
        )
        btn_copy_rgb.clicked.connect(self._copy_rgb)

        hex_col.addWidget(self.lbl_hex)
        hex_col.addWidget(self.lbl_rgb)
        hex_col.addWidget(btn_copy)
        hex_col.addWidget(btn_copy_rgb)

        preview_row.addWidget(self.preview)
        preview_row.addSpacing(16)
        preview_row.addLayout(hex_col)

        # Sliders
        self.slider_r = self._make_slider("#ff3355", 0)
        self.slider_g = self._make_slider("#00ff88", 255)
        self.slider_b = self._make_slider("#00ffff", 255)

        self.slider_r[0].valueChanged.connect(self._update)
        self.slider_g[0].valueChanged.connect(self._update)
        self.slider_b[0].valueChanged.connect(self._update)

        # Hex input
        hex_input_row = QHBoxLayout()
        lbl_hex_in    = QLabel("HEX:")
        lbl_hex_in.setStyleSheet("color:#444466;font-size:11px;")
        lbl_hex_in.setFixedWidth(36)

        self.hex_input = QLineEdit("#00FFFF")
        self.hex_input.setStyleSheet(
            "QLineEdit{background:#0a0a14;color:#cc00ff;"
            "border:1px solid #1a1a2e;padding:4px;"
            "font-family:monospace;font-size:12px;}"
        )
        self.hex_input.returnPressed.connect(self._apply_hex)

        hex_input_row.addWidget(lbl_hex_in)
        hex_input_row.addWidget(self.hex_input)

        layout.addWidget(lbl_h)
        layout.addLayout(preview_row)
        layout.addLayout(self.slider_r[1])
        layout.addLayout(self.slider_g[1])
        layout.addLayout(self.slider_b[1])
        layout.addLayout(hex_input_row)

        self.setLayout(layout)
        self._update()

    def _make_slider(self, color, initial):
        """Creates a labeled color slider row."""
        row = QHBoxLayout()
        row.setSpacing(8)

        letter = color[1].upper() if color[1] in 'rRgGbB' else '?'
        # Determine label from color
        if "ff33" in color:    letter = "R"
        elif "ff88" in color:  letter = "G"
        else:                  letter = "B"

        lbl = QLabel(letter)
        lbl.setFixedWidth(14)
        lbl.setStyleSheet(f"color:{color};font-weight:bold;font-size:13px;")

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(initial)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: #1a1a2e; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {color}; width: 14px; height: 14px;
                margin: -5px 0; border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color}; height: 4px; border-radius: 2px;
            }}
        """)

        val_lbl = QLabel(str(initial))
        val_lbl.setFixedWidth(28)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        val_lbl.setStyleSheet(
            f"color:{color};font-family:monospace;font-size:11px;"
        )

        slider.valueChanged.connect(
            lambda v, l=val_lbl: l.setText(str(v))
        )

        row.addWidget(lbl)
        row.addWidget(slider)
        row.addWidget(val_lbl)

        return slider, row

    def _update(self):
        """Recomputes color from sliders and updates all displays."""
        r = self.slider_r[0].value()
        g = self.slider_g[0].value()
        b = self.slider_b[0].value()

        color   = QColor(r, g, b)
        hex_str = color.name().upper()

        self.preview.set_color(color)
        self.lbl_hex.setText(hex_str)
        self.lbl_rgb.setText(f"R:{r}  G:{g}  B:{b}")
        self.lbl_hex.setStyleSheet(
            f"color:{hex_str};font-size:22px;"
            f"font-weight:bold;font-family:monospace;"
        )
        self.hex_input.setText(hex_str)

    def _apply_hex(self):
        """Parses hex input and sets sliders."""
        text  = self.hex_input.text().strip()
        color = QColor(text)
        if color.isValid():
            self.slider_r[0].setValue(color.red())
            self.slider_g[0].setValue(color.green())
            self.slider_b[0].setValue(color.blue())

    def _copy_hex(self):
        QApplication.clipboard().setText(self.lbl_hex.text())
        self.lbl_hex.setText("COPIED!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(
            800,
            lambda: self.lbl_hex.setText(self.hex_input.text())
        )

    def _copy_rgb(self):
        r = self.slider_r[0].value()
        g = self.slider_g[0].value()
        b = self.slider_b[0].value()
        QApplication.clipboard().setText(f"rgb({r}, {g}, {b})")


def create_app(manifest):
    return ColorPickerApp(manifest)