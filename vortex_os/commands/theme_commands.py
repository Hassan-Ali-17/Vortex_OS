# commands/theme_commands.py
# VORTEX OS - Theme and History Commands

import os
from themes.theme_engine import get_engine, THEMES
from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


@with_timestamp
def cmd_theme(args, config):
    """
    Command: theme [name]
    
    Without args  : shows all available themes
    theme <name>  : switches to that theme instantly
    theme preview : shows a color preview of current theme
    
    Examples:
        theme
        theme matrix
        theme blood
        theme preview
    """
    engine = get_engine()

    if not args:
        _theme_list(engine)
        return

    action = args[0].lower()

    if action == "preview":
        _theme_preview(engine)
        return

    if action == "list":
        _theme_list(engine)
        return

    # Try to switch theme
    success = engine.set_theme(action)

    if success:
        # Get the new colors immediately after switching
        print(f"\n{COLORS.SUCCESS}{COLORS.BOLD}  ◈ Theme switched to: "
              f"{THEMES[action]['name']}{COLORS.RESET}")
        print(f"  {COLORS.DIM}{THEMES[action]['description']}{COLORS.RESET}")
        print(f"  {COLORS.PRIMARY}Primary{COLORS.RESET}  "
              f"{COLORS.SUCCESS}Success{COLORS.RESET}  "
              f"{COLORS.ACCENT}Accent{COLORS.RESET}  "
              f"{COLORS.WARNING}Warning{COLORS.RESET}  "
              f"{COLORS.ERROR}Error{COLORS.RESET}")
        print(f"\n  {COLORS.DIM}Theme saved. Restart not required.{COLORS.RESET}\n")
    else:
        print(f"\n{COLORS.ERROR}  [!] Unknown theme: '{action}'{COLORS.RESET}")
        print(f"{COLORS.DIM}  Available: {', '.join(THEMES.keys())}{COLORS.RESET}\n")


def _theme_list(engine):
    """Displays all themes with active indicator."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ AVAILABLE THEMES{COLORS.RESET}")

    for name, desc, is_active in engine.list_themes():
        if is_active:
            marker = f"{COLORS.SUCCESS}●{COLORS.RESET}"
            label  = f"{COLORS.BOLD}{name.upper()}{COLORS.RESET}"
            tag    = f"{COLORS.SUCCESS} ← active{COLORS.RESET}"
        else:
            marker = f"{COLORS.DIM}○{COLORS.RESET}"
            label  = f"{COLORS.TEXT}{name}"
            tag    = ""

        print(f"  {marker} {label:<16}{COLORS.DIM}{desc}{tag}")

    print(f"\n  {COLORS.DIM}Usage: theme <name>{COLORS.RESET}\n")


def _theme_preview(engine):
    """Shows a live color preview of every semantic color in current theme."""
    name = engine.active_name.upper()
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ THEME PREVIEW — {name}{COLORS.RESET}\n")

    samples = [
        ("PRIMARY", "Interface elements, prompts"),
        ("SUCCESS", "Confirmations, OK messages"),
        ("WARNING", "Alerts, notices"),
        ("ERROR",   "Failures, critical messages"),
        ("ACCENT",  "Headers, highlights"),
        ("TEXT",    "Body text"),
        ("DIM",     "Secondary, metadata"),
    ]

    for key, description in samples:
        color = engine.get_color(key)
        bold  = engine.get_color("BOLD")
        reset = engine.get_color("RESET")
        print(f"  {color}{bold}{key:<12}{reset}  {color}{'█' * 8}{reset}  "
              f"{COLORS.DIM}{description}{COLORS.RESET}")

    print()


@with_timestamp
def cmd_history(args, config):
    """
    Command: history [n | clear]
    
    history        : shows last 15 commands
    history 30     : shows last 30 commands
    history clear  : clears all history
    """
    # History manager is injected into config by the shell
    history_mgr = config.get("_history")

    if args and args[0].lower() == "clear":
        if history_mgr:
            history_mgr.clear()
        print(f"\n{COLORS.SUCCESS}  ◈ History cleared.{COLORS.RESET}\n")
        return

    # How many entries to show
    try:
        n = int(args[0]) if args else 15
        n = max(1, min(n, 500))   # Clamp between 1 and 500
    except ValueError:
        print(f"{COLORS.ERROR}  [!] Usage: history [n | clear]{COLORS.RESET}\n")
        return

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ COMMAND HISTORY{COLORS.RESET}")

    if history_mgr:
        recent = history_mgr.get_recent(n)
        total  = history_mgr.count
    else:
        recent = []
        total  = 0

    if not recent:
        print(f"  {COLORS.DIM}No history yet.{COLORS.RESET}\n")
        return

    # Calculate starting index for display
    start_index = total - len(recent)

    for i, cmd in enumerate(recent, start=start_index + 1):
        print(f"  {COLORS.DIM}{i:>4}  {COLORS.TEXT}{cmd}")

    print(f"\n  {COLORS.DIM}{total} total entries.  "
          f"Use ↑↓ arrows to navigate.{COLORS.RESET}\n")