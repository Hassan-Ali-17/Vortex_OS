# gui/tab_bar.py
# VORTEX OS - Custom Tab Bar for Multi-Tab Terminal
# Fully styled tab row with add/close/rename support.

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton,
    QLabel, QInputDialog, QSizePolicy
)
from PyQt6.QtCore    import Qt, pyqtSignal, QSize
from PyQt6.QtGui     import QFont


# ── Stylesheet constants ──────────────────────────────────

TAB_BAR_BG = "#0a0a14"

TAB_INACTIVE = """
    QPushButton {
        background-color: #0a0a14;
        color: #444466;
        border: none;
        border-right: 1px solid #1a1a2e;
        border-bottom: 2px solid #1a1a2e;
        padding: 0px 8px;
        font-family: monospace;
        font-size: 11px;
        text-align: left;
    }
    QPushButton:hover {
        background-color: #111122;
        color: #8888aa;
    }
"""

TAB_ACTIVE = """
    QPushButton {
        background-color: #07070f;
        color: #00ffff;
        border: none;
        border-right: 1px solid #1a1a2e;
        border-bottom: 2px solid #00ffff;
        padding: 0px 8px;
        font-family: monospace;
        font-size: 11px;
        font-weight: bold;
        text-align: left;
    }
"""

TAB_CLOSE = """
    QPushButton {
        background-color: transparent;
        color: #333355;
        border: none;
        font-size: 11px;
        padding: 0px 4px;
        min-width: 16px;
        max-width: 16px;
    }
    QPushButton:hover {
        color: #ff3355;
    }
"""

TAB_NEW = """
    QPushButton {
        background-color: transparent;
        color: #444466;
        border: none;
        border-left: 1px solid #1a1a2e;
        font-size: 16px;
        padding: 0px 10px;
        min-width: 32px;
    }
    QPushButton:hover {
        color: #00ffff;
        background-color: #111122;
    }
"""


class TabButton(QWidget):
    """
    A single tab in the tab bar.

    Contains:
    - A main button (label text, click to activate)
    - A close button (× to close this tab)

    Emits:
    - clicked(index)      when the tab label is clicked
    - close_requested(index) when × is clicked
    - rename_requested(index) on double-click
    """

    clicked          = pyqtSignal(int)
    close_requested  = pyqtSignal(int)
    rename_requested = pyqtSignal(int)

    HEIGHT = 32

    def __init__(self, index, title, parent=None):
        super().__init__(parent)
        self.index     = index
        self._title    = title
        self._active   = False

        self.setFixedHeight(self.HEIGHT)
        self.setMinimumWidth(120)
        self.setMaximumWidth(220)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main label button
        self.btn_label = QPushButton(self._title)
        self.btn_label.setStyleSheet(TAB_INACTIVE)
        self.btn_label.setFixedHeight(self.HEIGHT)
        self.btn_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.btn_label.clicked.connect(
            lambda: self.clicked.emit(self.index)
        )
        self.btn_label.mouseDoubleClickEvent = (
            lambda e: self.rename_requested.emit(self.index)
        )

        # Close button
        self.btn_close = QPushButton("×")
        self.btn_close.setStyleSheet(TAB_CLOSE)
        self.btn_close.setFixedSize(20, self.HEIGHT)
        self.btn_close.clicked.connect(
            lambda: self.close_requested.emit(self.index)
        )

        layout.addWidget(self.btn_label)
        layout.addWidget(self.btn_close)
        self.setLayout(layout)

    def set_active(self, active):
        """Switches between active and inactive visual style."""
        self._active = active
        self.btn_label.setStyleSheet(
            TAB_ACTIVE if active else TAB_INACTIVE
        )

    def set_title(self, title):
        """Updates the tab label text."""
        self._title = title
        # Truncate long titles with ellipsis
        display = title if len(title) <= 22 else title[:20] + "…"
        self.btn_label.setText(display)
        self.btn_label.setToolTip(title)

    def update_index(self, new_index):
        """Updates stored index after tabs are reordered."""
        self.index = new_index


class TabBar(QWidget):
    """
    The full tab bar row.

    Manages a list of TabButton widgets and a + button.
    Emits signals that TabTerminal listens to.

    Signals:
        tab_clicked(index)        : user switched to a tab
        tab_close_requested(index): user closed a tab
        tab_rename_requested(index): user wants to rename
        new_tab_requested         : user clicked +
    """

    tab_clicked          = pyqtSignal(int)
    tab_close_requested  = pyqtSignal(int)
    tab_rename_requested = pyqtSignal(int)
    new_tab_requested    = pyqtSignal()

    HEIGHT = 32

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(f"background-color: {TAB_BAR_BG};")

        self._tabs = []   # List of TabButton widgets

        self._build_ui()

    def _build_ui(self):
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # + button always on the right
        self._btn_new = QPushButton("+")
        self._btn_new.setStyleSheet(TAB_NEW)
        self._btn_new.setFixedHeight(self.HEIGHT)
        self._btn_new.setFixedWidth(36)
        self._btn_new.clicked.connect(self.new_tab_requested.emit)

        self._layout.addWidget(self._btn_new)
        self._layout.addStretch(1)

        self.setLayout(self._layout)

    def add_tab(self, title):
        """
        Adds a new tab button and returns its index.
        Inserts before the + button.
        """
        index = len(self._tabs)
        tab   = TabButton(index, title)

        # Connect signals
        tab.clicked.connect(self.tab_clicked.emit)
        tab.close_requested.connect(self.tab_close_requested.emit)
        tab.rename_requested.connect(self.tab_rename_requested.emit)

        # Insert before the stretch + new button
        # The layout is: [tab0][tab1]...[+][stretch]
        # We insert at position = current tab count
        self._layout.insertWidget(index, tab)
        self._tabs.append(tab)

        return index

    def remove_tab(self, index):
        """
        Removes a tab button at index and re-numbers remaining tabs.
        """
        if index < 0 or index >= len(self._tabs):
            return

        tab = self._tabs.pop(index)
        self._layout.removeWidget(tab)
        tab.deleteLater()

        # Re-number remaining tabs so their stored indices are correct
        for i, t in enumerate(self._tabs):
            t.update_index(i)

    def set_active(self, index):
        """Highlights the tab at index, dims all others."""
        for i, tab in enumerate(self._tabs):
            tab.set_active(i == index)

    def set_tab_title(self, index, title):
        """Updates the display title of a tab."""
        if 0 <= index < len(self._tabs):
            self._tabs[index].set_title(title)

    def count(self):
        """Returns number of open tabs."""
        return len(self._tabs)