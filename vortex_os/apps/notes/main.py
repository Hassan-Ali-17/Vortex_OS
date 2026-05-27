# apps/notes/main.py
# VORTEX OS - Notes App

import json
import os
import datetime

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QListWidget,
    QListWidgetItem, QSplitter, QLineEdit, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui  import QFont

from apps.base_app import BaseApp

NOTES_FILE = "vault_storage/notes.json"


class NotesApp(BaseApp):
    """
    A persistent notes app.
    Notes are saved to vault_storage/notes.json.

    Features:
    - Create, edit, delete notes
    - Note list on the left, editor on the right
    - Auto-save on every keystroke
    - Timestamps on each note
    """

    def get_title(self):
        return "◧ VORTEX NOTES"

    def setup_ui(self):
        self.setMinimumSize(600, 420)
        self._notes      = []   # List of note dicts
        self._current_idx = -1
        self._saving     = False

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ─────────────────────────────
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(
            "background:#0d0d1a; border-bottom:1px solid #003333;"
        )
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 8, 0)

        lbl = QLabel("◧ VORTEX NOTES")
        lbl.setStyleSheet(
            "color:#cc00ff; font-size:11px; "
            "font-weight:bold; letter-spacing:3px;"
        )

        btn_new = QPushButton("+ NEW")
        btn_new.setFixedSize(70, 24)
        btn_new.setStyleSheet(
            "QPushButton{background:#0a0a14;color:#cc00ff;"
            "border:1px solid #660088;font-size:10px;padding:2px;}"
            "QPushButton:hover{background:#1a0a2e;border-color:#cc00ff;}"
        )
        btn_new.clicked.connect(self._new_note)

        btn_del = QPushButton("✕ DEL")
        btn_del.setFixedSize(70, 24)
        btn_del.setStyleSheet(
            "QPushButton{background:#0a0a14;color:#ff3355;"
            "border:1px solid #550022;font-size:10px;padding:2px;}"
            "QPushButton:hover{background:#1a0a0a;border-color:#ff3355;}"
        )
        btn_del.clicked.connect(self._delete_note)

        h_layout.addWidget(lbl)
        h_layout.addStretch()
        h_layout.addWidget(btn_new)
        h_layout.addWidget(btn_del)
        header.setLayout(h_layout)

        # ── Splitter: list | editor ─────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Note list
        self.note_list = QListWidget()
        self.note_list.setFixedWidth(180)
        self.note_list.setStyleSheet(
            "QListWidget{background:#0a0a14;border:none;"
            "border-right:1px solid #1a1a2e;}"
            "QListWidget::item{color:#888899;padding:8px;"
            "border-bottom:1px solid #0d0d1a;}"
            "QListWidget::item:selected{background:#1a1a2e;"
            "color:#cc00ff;}"
        )
        self.note_list.currentRowChanged.connect(self._on_note_selected)

        # Editor panel
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        # Title input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Note title...")
        self.title_input.setFixedHeight(36)
        self.title_input.setStyleSheet(
            "QLineEdit{background:#0d0d1a;color:#cc00ff;"
            "border:none;border-bottom:1px solid #1a1a2e;"
            "padding:8px;font-size:13px;font-weight:bold;}"
        )
        self.title_input.textChanged.connect(self._on_content_changed)

        # Body editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Start typing your note...\n\nAuto-saved to vx://vault"
        )
        self.editor.setStyleSheet(
            "QTextEdit{background:#07070f;color:#e0e0ff;"
            "border:none;padding:12px;font-size:12px;}"
        )
        self.editor.textChanged.connect(self._on_content_changed)

        # Timestamp
        self.lbl_ts = QLabel("")
        self.lbl_ts.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_ts.setStyleSheet(
            "color:#333355;font-size:9px;padding:4px 8px;"
            "background:#0a0a14;border-top:1px solid #0d0d1a;"
        )

        editor_layout.addWidget(self.title_input)
        editor_layout.addWidget(self.editor, 1)
        editor_layout.addWidget(self.lbl_ts)
        editor_widget.setLayout(editor_layout)

        splitter.addWidget(self.note_list)
        splitter.addWidget(editor_widget)
        splitter.setStretchFactor(1, 1)
        splitter.setStyleSheet(
            "QSplitter::handle{background:#1a1a2e;width:1px;}"
        )

        layout.addWidget(header)
        layout.addWidget(splitter, 1)
        self.setLayout(layout)

        self._load_notes()

    def _load_notes(self):
        """Loads notes from vault_storage/notes.json."""
        try:
            with open(NOTES_FILE, 'r') as f:
                self._notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._notes = []

        self._refresh_list()

        if self._notes:
            self.note_list.setCurrentRow(0)

    def _save_notes(self):
        """Persists notes to disk."""
        if self._saving:
            return
        try:
            os.makedirs("vault_storage", exist_ok=True)
            with open(NOTES_FILE, 'w') as f:
                json.dump(self._notes, f, indent=2)
        except Exception as e:
            print(f"[Notes] Save error: {e}")

    def _refresh_list(self):
        """Redraws the note list widget."""
        self.note_list.clear()
        for note in self._notes:
            item = QListWidgetItem(note.get("title", "Untitled"))
            self.note_list.addItem(item)

    def _new_note(self):
        """Creates a blank new note and selects it."""
        note = {
            "title":   "New Note",
            "body":    "",
            "created": datetime.datetime.now().isoformat(),
            "modified":datetime.datetime.now().isoformat(),
        }
        self._notes.append(note)
        self._refresh_list()
        self.note_list.setCurrentRow(len(self._notes) - 1)
        self.title_input.setFocus()
        self.title_input.selectAll()

    def _delete_note(self):
        """Deletes the currently selected note."""
        idx = self.note_list.currentRow()
        if idx < 0 or idx >= len(self._notes):
            return
        self._notes.pop(idx)
        self._save_notes()
        self._refresh_list()

        # Select nearest remaining note
        new_count = len(self._notes)
        if new_count > 0:
            self.note_list.setCurrentRow(min(idx, new_count - 1))
        else:
            self.title_input.clear()
            self.editor.clear()
            self.lbl_ts.setText("")
            self._current_idx = -1

    def _on_note_selected(self, row):
        """Loads the selected note into the editor."""
        if row < 0 or row >= len(self._notes):
            return

        self._saving      = True   # Prevent save loop
        self._current_idx = row
        note              = self._notes[row]

        self.title_input.setText(note.get("title", ""))
        self.editor.setPlainText(note.get("body", ""))

        modified = note.get("modified", "")
        if modified:
            try:
                dt  = datetime.datetime.fromisoformat(modified)
                self.lbl_ts.setText(
                    f"Modified: {dt.strftime('%Y-%m-%d %H:%M')}"
                )
            except Exception:
                self.lbl_ts.setText("")

        self._saving = False

    def _on_content_changed(self):
        """Called on every keystroke — auto-saves the current note."""
        if self._saving or self._current_idx < 0:
            return
        if self._current_idx >= len(self._notes):
            return

        note = self._notes[self._current_idx]
        note["title"]    = self.title_input.text() or "Untitled"
        note["body"]     = self.editor.toPlainText()
        note["modified"] = datetime.datetime.now().isoformat()

        # Update list item text
        item = self.note_list.item(self._current_idx)
        if item:
            item.setText(note["title"])

        self._save_notes()


def create_app(manifest):
    return NotesApp(manifest)