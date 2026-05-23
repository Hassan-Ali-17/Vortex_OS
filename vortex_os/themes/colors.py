# themes/colors.py
# VORTEX OS - Color Module (Phase 3+)
# Now delegates to the theme engine.
# Other files that import from here still work unchanged.

from themes.theme_engine import COLORS, get_engine

# Keep this for any code that imports CyberpunkColors directly
from colorama import Fore, Style, init
init(autoreset=True)


class CyberpunkColors:
    """Legacy compatibility class. Use COLORS from theme_engine instead."""
    PRIMARY = Fore.CYAN
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR   = Fore.RED
    ACCENT  = Fore.MAGENTA
    TEXT    = Fore.WHITE
    DIM     = Fore.LIGHTBLACK_EX
    BOLD    = Style.BRIGHT
    RESET   = Style.RESET_ALL