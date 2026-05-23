# terminal/history.py
# VORTEX OS - Command History Manager
# Saves/loads history and integrates with readline for arrow-key navigation.

import json
import os
import readline   # Built-in Python module — no install needed


class HistoryManager:
    """
    Manages VORTEX terminal command history.
    
    Two layers:
    1. readline integration  — gives ↑↓ arrow key navigation live
    2. JSON persistence      — saves history between sessions
    
    Why both?
    readline handles the in-session experience (arrow keys).
    JSON handles cross-session persistence (history survives restarts).
    """

    def __init__(self, history_path="config/history.json", max_entries=500):
        self.history_path = history_path
        self.max_entries  = max_entries
        self._history     = []   # In-memory list

        self._setup_readline()
        self._load_history()

    def _setup_readline(self):
        """
        Configures the readline library.
        
        readline intercepts the input() call and adds:
        - ↑ / ↓  : navigate history
        - ←  / → : move cursor within line
        - Home/End: jump to start/end of line
        - Ctrl+A  : start of line
        - Ctrl+E  : end of line
        - Ctrl+U  : clear line
        - Backspace: delete character
        
        All of this for FREE with two lines of config.
        """
        # Use Emacs-style key bindings (standard terminal behavior)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind('"\\e[A": history-search-backward')
        readline.parse_and_bind('"\\e[B": history-search-forward')

        # Set history length limit in readline itself
        readline.set_history_length(self.max_entries)

    def _load_history(self):
        """
        Loads saved history from JSON and feeds it into readline.
        This is what makes previous sessions' history available
        immediately when VORTEX starts.
        """
        try:
            with open(self.history_path, 'r') as f:
                data = json.load(f)
            self._history = data.get("history", [])

            # Feed each saved command into readline's history buffer
            for cmd in self._history:
                if cmd.strip():
                    readline.add_history(cmd)

        except (FileNotFoundError, json.JSONDecodeError):
            self._history = []

    def add(self, command):
        """
        Adds a command to history.
        
        Rules:
        - Skip empty strings
        - Skip commands that are identical to the last entry
          (prevents 'help help help help' from spamming history)
        - Trim to max_entries
        """
        command = command.strip()

        if not command:
            return

        # Avoid consecutive duplicates
        if self._history and self._history[-1] == command:
            return

        self._history.append(command)

        # Trim oldest entries if over limit
        if len(self._history) > self.max_entries:
            self._history = self._history[-self.max_entries:]

        # readline already saw the command via input() — no need to
        # manually add it, but we do need to persist it
        self._save_history()

    def _save_history(self):
        """Persists history list to JSON file."""
        try:
            with open(self.history_path, 'w') as f:
                json.dump({
                    "history":     self._history,
                    "max_entries": self.max_entries
                }, f, indent=2)
        except Exception as e:
            pass   # History save failure is non-critical

    def get_recent(self, n=10):
        """Returns the last n commands."""
        return self._history[-n:]
    
    def get_all(self):
     """Returns the complete history list."""
     return list(self._history)

    def clear(self):
        """Clears all history."""
        self._history = []
        readline.clear_history()
        self._save_history()

    @property
    def count(self):
        return len(self._history)