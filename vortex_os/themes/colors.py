# themes/colors.py
# VORTEX OS - Color Theme Engine (Phase 1: Basic Colors)
# Uses colorama for cross-platform terminal color support

from colorama import Fore, Back, Style, init

# Initialize colorama
# auto_reset=True means colors reset automatically after each print
init(autoreset=True)


class CyberpunkColors:
    """
    Cyberpunk color palette for VORTEX OS terminal.
    All colors are defined as class attributes so they can be
    accessed like: CyberpunkColors.PRIMARY
    """

    # Primary interface color - cyan/electric blue
    PRIMARY   = Fore.CYAN
    
    # Success messages, confirmations
    SUCCESS   = Fore.GREEN
    
    # Warnings, important notices
    WARNING   = Fore.YELLOW
    
    # Errors, failures
    ERROR     = Fore.RED
    
    # Highlighted text, titles
    ACCENT    = Fore.MAGENTA
    
    # Normal body text (white)
    TEXT      = Fore.WHITE
    
    # Dimmed text, secondary info
    DIM       = Fore.LIGHTBLACK_EX
    
    # Bold styling
    BOLD      = Style.BRIGHT
    
    # Reset all styling
    RESET     = Style.RESET_ALL


# Convenience shortcut — other files can just import COLORS
COLORS = CyberpunkColors()