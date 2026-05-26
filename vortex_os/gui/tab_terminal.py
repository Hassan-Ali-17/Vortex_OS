# gui/tab_terminal.py
# VORTEX OS - Multi-Tab Terminal Container
# Manages multiple independent terminal sessions as tabs.

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
    QInputDialog, QSizePolicy, QSizeGrip,
    QHBoxLayout
)
from PyQt6.QtCore    import Qt, pyqtSignal, QTimer
from PyQt6.QtGui     import QKeySequence, QShortcut

from gui.tab_bar         import TabBar
from gui.terminal_widget import EmbeddedTerminal
from core.filesystem     import get_vfs


class TabTerminal(QWidget):
    """
    Multi-tab terminal widget for the VORTEX desktop.

    Each tab contains one EmbeddedTerminal instance.
    Tabs are independent — different CWD, history, state.

    The tab title updates every 2 seconds to reflect the
    current working directory of that session's terminal.

    Signals:
        closed : emitted when the user closes the whole panel
    """

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 380)

        # Tracks CWD per tab for title updates
        # Key: tab index, Value: last known cwd string
        self._tab_cwds = {}

        self._build_ui()
        self._setup_shortcuts()

        # Open the first tab automatically
        self.add_tab()

        # Timer: updates tab titles with current directory
        self._title_timer = QTimer(self)
        self._title_timer.timeout.connect(self._refresh_tab_titles)
        self._title_timer.start(2000)

    def _build_ui(self):
        """Assembles the tab bar + stacked terminal area."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Title row: label + close button ───────
        from PyQt6.QtWidgets import QLabel, QPushButton
        title_row = QWidget()
        title_row.setFixedHeight(28)
        title_row.setStyleSheet(
            "background-color: #0d0d1a;"
            "border-bottom: 1px solid #003333;"
        )
        tr_layout = QHBoxLayout()
        tr_layout.setContentsMargins(8, 0, 0, 0)
        tr_layout.setSpacing(0)

        lbl = QLabel("▶ VORTEX TERMINAL")
        lbl.setStyleSheet(
            "color: #00ffff; font-size: 10px; font-weight: bold;"
            "font-family: monospace; letter-spacing: 2px;"
        )

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(
            "QPushButton { background: transparent; color: #333355;"
            "border: none; font-size: 13px; }"
            "QPushButton:hover { color: #ff3355; }"
        )
        btn_close.clicked.connect(self._on_close)

        tr_layout.addWidget(lbl)
        tr_layout.addStretch()
        tr_layout.addWidget(btn_close)
        title_row.setLayout(tr_layout)

        # ── Tab bar ────────────────────────────────
        self.tab_bar = TabBar()
        self.tab_bar.tab_clicked.connect(self._on_tab_clicked)
        self.tab_bar.tab_close_requested.connect(self._on_tab_close)
        self.tab_bar.tab_rename_requested.connect(self._on_tab_rename)
        self.tab_bar.new_tab_requested.connect(self.add_tab)

        # ── Stacked terminal area ──────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #07070f;")
        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # ── Resize grip ────────────────────────────
        grip_row = QWidget()
        grip_row.setFixedHeight(14)
        grip_row.setStyleSheet("background-color: #07070f;")
        grip_layout = QHBoxLayout()
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()

        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(14, 14)
        self._grip.setStyleSheet(
            "QSizeGrip {"
            "    border-left: 2px solid #00ffff;"
            "    border-bottom: 2px solid #00ffff;"
            "    background: transparent;"
            "}"
            "QSizeGrip:hover {"
            "    border-left: 2px solid #ffffff;"
            "    border-bottom: 2px solid #ffffff;"
            "}"
        )
        grip_layout.addWidget(self._grip)
        grip_row.setLayout(grip_layout)

        # ── Assemble ───────────────────────────────
        layout.addWidget(title_row)
        layout.addWidget(self.tab_bar)
        layout.addWidget(self.stack, 1)
        layout.addWidget(grip_row)

        self.setLayout(layout)

    def _setup_shortcuts(self):
     """
    Keyboard shortcuts — only active when this widget has focus.

    Ctrl+T          → new tab
    Ctrl+W          → close current tab
    Ctrl+Tab        → next tab
    Ctrl+Shift+Tab  → previous tab
    Ctrl+1 to Ctrl+5 → jump directly to tab 1–5
     """
     sc_new = QShortcut(QKeySequence("Ctrl+T"), self)
     sc_new.activated.connect(self.add_tab)

     sc_close = QShortcut(QKeySequence("Ctrl+W"), self)
     sc_close.activated.connect(self._close_current_tab)
 
     sc_next = QShortcut(QKeySequence("Ctrl+Tab"), self)
     sc_next.activated.connect(self._next_tab)

     sc_prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
     sc_prev.activated.connect(self._prev_tab)

    # ── Ctrl+1 through Ctrl+5 ─────────────────────────────
    # Jump directly to a tab by number.
    #
    # Why loop with lambda i=i?
    # Python closures capture variables by reference, not value.
    # Without the default argument trick (i=i), every lambda
    # would capture the SAME variable i — and after the loop
    # finishes, i=4 for all of them. Every shortcut would
    # jump to tab 5.
    #
    # With i=i, each lambda gets its OWN copy of i frozen
    # at the moment it was created. So:
    #   i=0 → Ctrl+1 jumps to tab index 0 (tab 1)
    #   i=1 → Ctrl+2 jumps to tab index 1 (tab 2)
    #   ... and so on.
    #
    # Tab numbers are 1-based for the user (Ctrl+1 = first tab)
    # but 0-based internally (_switch_to uses 0-based index).

     for i in range(5):
        sc = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
        sc.activated.connect(lambda checked=False, idx=i: self._switch_to(idx))

    # ─────────────────────────────────────────────
    #  TAB MANAGEMENT
    # ─────────────────────────────────────────────

    def add_tab(self, title=None):
        """
        Creates a new terminal session tab.

        Steps:
        1. Create an EmbeddedTerminal instance
        2. Add it to the QStackedWidget
        3. Add a TabButton to the TabBar
        4. Switch to the new tab
        5. Focus the input line

        Args:
            title : optional tab title. Defaults to 'vx://core'
                    or whatever the new terminal's CWD resolves to.
        """
        # Create terminal session
        terminal = EmbeddedTerminal()

        # Connect the command_finished signal for status output
        index = self.stack.count()
        terminal.command_finished.connect(
            lambda cmd, elapsed, i=index:
                self._on_command_finished(i, cmd, elapsed)
        )

        # Add to stack
        self.stack.addWidget(terminal)

        # Determine initial title
        if title is None:
            try:
                vfs   = get_vfs()
                cwd   = os.getcwd()
                title = vfs.display_path(cwd)
            except Exception:
                title = "terminal"

        # Add to tab bar
        tab_index = self.tab_bar.add_tab(title)

        # Switch to new tab
        self._switch_to(tab_index)

        # Focus input
        QTimer.singleShot(50, terminal.input_line.setFocus)

        return tab_index

    def _switch_to(self, index):
        """
        Switches the visible terminal to the tab at index.

        Updates:
        - QStackedWidget current index
        - TabBar active tab highlight
        - Window focus to the terminal input
        """
        if index < 0 or index >= self.stack.count():
            return

        self.stack.setCurrentIndex(index)
        self.tab_bar.set_active(index)

        # Focus the input line of the now-visible terminal
        terminal = self.stack.widget(index)
        if terminal:
            QTimer.singleShot(30, terminal.input_line.setFocus)

    def _close_current_tab(self):
        """Closes the currently active tab."""
        index = self.stack.currentIndex()
        self._on_tab_close(index)

    def _next_tab(self):
        """Cycles to the next tab (wraps around)."""
        current = self.stack.currentIndex()
        total   = self.stack.count()
        if total > 1:
            self._switch_to((current + 1) % total)

    def _prev_tab(self):
        """Cycles to the previous tab (wraps around)."""
        current = self.stack.currentIndex()
        total   = self.stack.count()
        if total > 1:
            self._switch_to((current - 1) % total)

    # ─────────────────────────────────────────────
    #  SIGNAL HANDLERS
    # ─────────────────────────────────────────────

    def _on_tab_clicked(self, index):
        """User clicked a tab label — switch to it."""
        self._switch_to(index)

    def _on_tab_close(self, index):
        """
        User clicked × on a tab.

        Rules:
        - If only one tab remains, hide the whole terminal panel
          instead of leaving an empty container.
        - If closing the active tab, switch to the nearest remaining tab.
        - Always clean up the EmbeddedTerminal widget properly.
        """
        total = self.stack.count()

        # Last tab — hide the whole panel
        if total <= 1:
            self._on_close()
            return

        # Remove from stack
        widget = self.stack.widget(index)
        if widget:
            self.stack.removeWidget(widget)
            widget.deleteLater()

        # Remove from tab bar
        self.tab_bar.remove_tab(index)

        # Remove from CWD tracking
        if index in self._tab_cwds:
            del self._tab_cwds[index]

        # Rebuild CWD tracking dict with new indices
        new_cwds = {}
        for old_idx, cwd in self._tab_cwds.items():
            new_idx = old_idx if old_idx < index else old_idx - 1
            new_cwds[new_idx] = cwd
        self._tab_cwds = new_cwds

        # Switch to nearest valid tab
        new_count = self.stack.count()
        new_index = min(index, new_count - 1)
        self._switch_to(new_index)

    def _on_tab_rename(self, index):
        """
        User double-clicked a tab — show rename dialog.
        QInputDialog is a built-in Qt dialog — no custom widget needed.
        """
        current_title = self.tab_bar._tabs[index]._title

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Tab",
            "Enter new tab name:",
            text=current_title
        )

        if ok and new_name.strip():
            self.tab_bar.set_tab_title(index, new_name.strip())

    def _on_command_finished(self, tab_index, command, elapsed):
        """
        Called when a command finishes in any tab.
        Prints status to console.
        """
        display = command[:28] + "…" if len(command) > 28 else command
        print(f"  ◈ tab[{tab_index}] done  [{display}]  {elapsed:.2f}s")

    def _on_close(self):
        """Hides the terminal panel and emits closed signal."""
        self.hide()
        self.closed.emit()

    # ─────────────────────────────────────────────
    #  TITLE UPDATES
    # ─────────────────────────────────────────────

    def _refresh_tab_titles(self):
        """
        Runs every 2 seconds.
        Updates each tab's title to the terminal's current directory.

        Why poll instead of using a signal?
        EmbeddedTerminal doesn't track CWD changes directly —
        commands like 'vault go' call os.chdir() which changes
        the process CWD globally. We read it back periodically.

        This is a known limitation — Phase 9 will improve it
        with a proper CWD-changed signal from vault go.
        """
        try:
            vfs = get_vfs()
        except Exception:
            return

        for i in range(self.stack.count()):
            terminal = self.stack.widget(i)
            if terminal is None:
                continue

            # Read the global CWD — this is approximate since all
            # tabs share the same process CWD (os.chdir is global).
            # True per-tab CWD tracking comes in a future improvement.
            try:
                cwd   = os.getcwd()
                title = vfs.display_path(cwd)
            except Exception:
                title = "terminal"

            # Only update if changed (avoids unnecessary redraws)
            if self._tab_cwds.get(i) != title:
                self._tab_cwds[i] = title
                # Only auto-update title if user hasn't renamed this tab
                # (We detect rename by checking if title looks like a vx:// path)
                current = self.tab_bar._tabs[i]._title if i < self.tab_bar.count() else ""
                if current.startswith("vx://") or current == "terminal":
                    self.tab_bar.set_tab_title(i, title)

    def resizeEvent(self, event):
        """Keep grip anchored to bottom-right on resize."""
        super().resizeEvent(event)
        if hasattr(self, '_grip'):
            self._grip.move(
                self.width()  - self._grip.width(),
                self.height() - self._grip.height()
            )