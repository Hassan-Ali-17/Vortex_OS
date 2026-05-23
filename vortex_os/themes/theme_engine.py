# themes/theme_engine.py
# VORTEX OS - Theme Engine
# Manages multiple color palettes and live theme switching.

import json
import os
from colorama import Fore, Back, Style, init

init(autoreset=True)


# ─────────────────────────────────────────────
#  THEME DEFINITIONS
#  Each theme is a dict mapping semantic names
#  to colorama color codes.
#  Semantic names (PRIMARY, ERROR, etc.) stay
#  the same — only the colors change.
# ─────────────────────────────────────────────

THEMES = {

    "cyberpunk": {
        "name":        "CYBERPUNK",
        "description": "Electric cyan on black. The classic.",
        "PRIMARY":     Fore.CYAN,
        "SUCCESS":     Fore.GREEN,
        "WARNING":     Fore.YELLOW,
        "ERROR":       Fore.RED,
        "ACCENT":      Fore.MAGENTA,
        "TEXT":        Fore.WHITE,
        "DIM":         Fore.LIGHTBLACK_EX,
        "BOLD":        Style.BRIGHT,
        "RESET":       Style.RESET_ALL,
    },

    "matrix": {
        "name":        "MATRIX",
        "description": "All green. Follow the white rabbit.",
        "PRIMARY":     Fore.LIGHTGREEN_EX,
        "SUCCESS":     Fore.GREEN,
        "WARNING":     Fore.YELLOW,
        "ERROR":       Fore.RED,
        "ACCENT":      Fore.GREEN,
        "TEXT":        Fore.LIGHTGREEN_EX,
        "DIM":         Fore.GREEN,
        "BOLD":        Style.BRIGHT,
        "RESET":       Style.RESET_ALL,
    },

    "blood": {
        "name":        "BLOOD",
        "description": "Red and white. Danger mode.",
        "PRIMARY":     Fore.LIGHTRED_EX,
        "SUCCESS":     Fore.WHITE,
        "WARNING":     Fore.YELLOW,
        "ERROR":       Fore.RED,
        "ACCENT":      Fore.RED,
        "TEXT":        Fore.WHITE,
        "DIM":         Fore.LIGHTBLACK_EX,
        "BOLD":        Style.BRIGHT,
        "RESET":       Style.RESET_ALL,
    },

    "ghost": {
        "name":        "GHOST",
        "description": "White and grey. Minimal stealth mode.",
        "PRIMARY":     Fore.WHITE,
        "SUCCESS":     Fore.LIGHTWHITE_EX,
        "WARNING":     Fore.YELLOW,
        "ERROR":       Fore.LIGHTRED_EX,
        "ACCENT":      Fore.LIGHTWHITE_EX,
        "TEXT":        Fore.LIGHTWHITE_EX,
        "DIM":         Fore.LIGHTBLACK_EX,
        "BOLD":        Style.BRIGHT,
        "RESET":       Style.RESET_ALL,
    },

    "solar": {
        "name":        "SOLAR",
        "description": "Amber and gold. Warm retro terminal.",
        "PRIMARY":     Fore.YELLOW,
        "SUCCESS":     Fore.LIGHTYELLOW_EX,
        "WARNING":     Fore.LIGHTRED_EX,
        "ERROR":       Fore.RED,
        "ACCENT":      Fore.LIGHTYELLOW_EX,
        "TEXT":        Fore.LIGHTYELLOW_EX,
        "DIM":         Fore.LIGHTBLACK_EX,
        "BOLD":        Style.BRIGHT,
        "RESET":       Style.RESET_ALL,
    },

    "arctic": {
        "name":        "ARCTIC",
        "description": "Ice blue and white. Cool and clean.",
        "PRIMARY":     Fore.LIGHTCYAN_EX,
        "SUCCESS":     Fore.CYAN,
        "WARNING":     Fore.YELLOW,
        "ERROR":       Fore.LIGHTRED_EX,
        "ACCENT":      Fore.LIGHTBLUE_EX,
        "TEXT":        Fore.WHITE,
        "DIM":         Fore.LIGHTBLACK_EX,
        "BOLD":        Style.BRIGHT,
        "RESET":       Style.RESET_ALL,
    },
}


class ThemeEngine:
    """
    Manages the active color theme for VORTEX OS.
    
    Usage pattern:
        engine = ThemeEngine()
        engine.set_theme("matrix")
        
        # Then import COLORS from the engine's active proxy
        from themes.theme_engine import COLORS
        print(COLORS.PRIMARY + "Hello")
    
    The proxy object dynamically reads from the active theme,
    so all existing code using COLORS.PRIMARY etc. works
    without any modification.
    """

    def __init__(self, config_path="config/settings.json"):
        self.config_path   = config_path
        self._active_name  = "cyberpunk"
        self._active_theme = THEMES["cyberpunk"]
        self._load_saved_theme()

    def _load_saved_theme(self):
        """Reads the last-used theme from settings.json."""
        try:
            with open(self.config_path, 'r') as f:
                cfg = json.load(f)
            saved = cfg.get("default_theme", "cyberpunk")
            if saved in THEMES:
                self._active_name  = saved
                self._active_theme = THEMES[saved]
        except (FileNotFoundError, json.JSONDecodeError):
            pass   # Use default cyberpunk

    def _save_theme(self, theme_name):
        """Persists the chosen theme to settings.json."""
        try:
            with open(self.config_path, 'r') as f:
                cfg = json.load(f)
            cfg["default_theme"] = theme_name
            with open(self.config_path, 'w') as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            print(f"[WARN] Could not save theme: {e}")

    def set_theme(self, name):
        """
        Switches the active theme by name.
        
        Returns True on success, False if theme not found.
        """
        name = name.lower()
        if name not in THEMES:
            return False

        self._active_name  = name
        self._active_theme = THEMES[name]
        self._save_theme(name)
        return True

    def get_color(self, key):
        """Returns a color code from the active theme by key."""
        return self._active_theme.get(key, "")

    @property
    def active_name(self):
        return self._active_name

    @property
    def active_theme(self):
        return self._active_theme

    def list_themes(self):
        """Returns list of (name, description, is_active) tuples."""
        return [
            (name, data["description"], name == self._active_name)
            for name, data in THEMES.items()
        ]


# ─────────────────────────────────────────────
#  GLOBAL ENGINE INSTANCE
#  One engine instance shared across the whole app.
#  All modules import this single instance.
# ─────────────────────────────────────────────

_engine = ThemeEngine()


class _ColorProxy:
    """
    A proxy object that makes theme colors accessible as attributes.
    
    Instead of:
        color = _engine.get_color("PRIMARY")
    
    You write:
        COLORS.PRIMARY
    
    The __getattr__ method intercepts attribute access and
    looks it up in the active theme dynamically.
    This means COLORS.PRIMARY always returns the CURRENT
    theme's primary color, even after theme switches.
    """

    def __getattr__(self, name):
        # Try to get from active theme
        value = _engine.get_color(name)
        if value:
            return value
        # Unknown attribute — return empty string, don't crash
        return ""


# This is what all other files import
COLORS = _ColorProxy()


def get_engine():
    """Returns the global ThemeEngine instance."""
    return _engine