# commands/theme_commands.py
# VORTEX OS - Theme and History Commands

import os
from themes.theme_engine import get_engine, THEMES
from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


@with_timestamp
def cmd_theme(args, config):
    """
    Command: theme [name | list | preview | animate]
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

    if action == "animate":             # ← ADD THIS BLOCK
        theme_animate(engine)
        return

    # Switch theme
    success = engine.set_theme(action)

    if success:
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

def theme_animate(engine):
    """
    Cycles through every available theme with a live preview.
    Restores the original theme when done or if interrupted.

    Flow:
    1. Save current theme name
    2. For each theme: switch → clear screen → show preview → wait 1s
    3. After loop (or on Ctrl+C): restore original theme
    4. Print confirmation

    Why use try/finally?
    finally always runs — even if an exception happens mid-loop.
    This guarantees the original theme is always restored.
    """
    import time
    import os

    original_theme = engine.active_name
    theme_names    = list(THEMES.keys())
    total          = len(theme_names)

    print(f"\n{COLORS.ACCENT}  ◈ THEME ANIMATION — {total} themes{COLORS.RESET}")
    print(f"  {COLORS.DIM}Press Ctrl+C to stop early.{COLORS.RESET}\n")
    time.sleep(0.8)

    try:
        for i, name in enumerate(theme_names, start=1):
            # Switch to this theme
            engine.set_theme(name)

            # Clear screen for clean display
            os.system('clear')

            theme_data = THEMES[name]

            # Build the display using the NEW theme's colors directly
            # We can't use COLORS.X here because the proxy updates
            # instantly — so COLORS.PRIMARY IS the new theme's primary.
            primary = engine.get_color("PRIMARY")
            accent  = engine.get_color("ACCENT")
            success = engine.get_color("SUCCESS")
            warning = engine.get_color("WARNING")
            error   = engine.get_color("ERROR")
            dim     = engine.get_color("DIM")
            bold    = engine.get_color("BOLD")
            reset   = engine.get_color("RESET")

            # Header
            print(f"\n{accent}{bold}{'═'*52}{reset}")
            print(f"{accent}{bold}  VORTEX THEME PREVIEW  [{i}/{total}]{reset}")
            print(f"{accent}{bold}{'═'*52}{reset}\n")

            # Theme name and description
            print(f"  {primary}{bold}{theme_data['name']}{reset}")
            print(f"  {dim}{theme_data['description']}{reset}\n")

            # Color swatches
            swatches = [
                ("PRIMARY", primary),
                ("SUCCESS", success),
                ("WARNING", warning),
                ("ERROR",   error),
                ("ACCENT",  accent),
            ]

            for label, color in swatches:
                bar = '█' * 16
                print(f"  {color}{bold}{label:<12}{reset}  {color}{bar}{reset}")

            # Sample prompt
            print(f"\n  {dim}Sample prompt:{reset}")
            print(f"  {primary}{bold}[VORTEX@CORE ~/vortex_os] > {reset}"
                  f"{accent}clock{reset}")

            # Progress bar at the bottom
            progress_filled = int((i / total) * 30)
            progress_bar    = '▓' * progress_filled + '░' * (30 - progress_filled)
            print(f"\n  {dim}[{progress_bar}]  {i}/{total}{reset}")
            print(f"\n  {dim}Next in 1.5s... Ctrl+C to stop{reset}")

            time.sleep(1.5)

    except KeyboardInterrupt:
        # User stopped early — that's fine
        pass

    finally:
        # This ALWAYS runs — restore original theme no matter what
        engine.set_theme(original_theme)
        os.system('clear')
        print(f"\n{COLORS.SUCCESS}  ◈ Animation complete. "
              f"Restored theme: {original_theme.upper()}{COLORS.RESET}\n")


@with_timestamp
def cmd_history(args, config):
    """
    Command: history [n | clear | search <word>]
    
    history              : shows last 15 commands
    history 30           : shows last 30 commands
    history clear        : clears all history
    history search <word>: filters history by keyword
    """
    history_mgr = config.get("_history")

    # ── CLEAR ──────────────────────────────────────
    if args and args[0].lower() == "clear":
        if history_mgr:
            history_mgr.clear()
        print(f"\n{COLORS.SUCCESS}  ◈ History cleared.{COLORS.RESET}\n")
        return

    # ── SEARCH ─────────────────────────────────────
    if args and args[0].lower() == "search":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: history search <word>{COLORS.RESET}\n")
            return
        keyword = args[1].lower()
        _history_search(history_mgr, keyword)
        return

    # ── SHOW LAST N ────────────────────────────────
    try:
        n = int(args[0]) if args else 15
        n = max(1, min(n, 500))
    except ValueError:
        print(f"{COLORS.ERROR}  [!] Usage: history [n | clear | search <word>]{COLORS.RESET}\n")
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

    start_index = total - len(recent)
    for i, cmd in enumerate(recent, start=start_index + 1):
        print(f"  {COLORS.DIM}{i:>4}  {COLORS.TEXT}{cmd}")

    print(f"\n  {COLORS.DIM}{total} total entries. "
          f"Use ↑↓ arrows to navigate.{COLORS.RESET}\n")


def _history_search(history_mgr, keyword):
    """
    Searches through ALL history entries for lines containing keyword.
    Case-insensitive. Shows line number, highlights the match in color.

    Why search ALL entries and not just recent?
    Because the whole point of search is to find something
    you typed a long time ago that's not in the recent window.
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ HISTORY SEARCH — '{keyword}'{COLORS.RESET}\n")

    if not history_mgr:
        print(f"  {COLORS.DIM}No history manager available.{COLORS.RESET}\n")
        return

    all_history = history_mgr.get_all()
    matches     = []

    for i, cmd in enumerate(all_history, start=1):
        if keyword in cmd.lower():
            matches.append((i, cmd))

    if not matches:
        print(f"  {COLORS.DIM}No matches found for '{keyword}'.{COLORS.RESET}\n")
        return

    for index, cmd in matches:
        # Highlight the matching portion inside the command string.
        # We find where the keyword is (case-insensitive), then wrap
        # that slice in color codes so it stands out visually.
        lower_cmd = cmd.lower()
        pos       = lower_cmd.find(keyword)

        if pos >= 0:
            before  = cmd[:pos]
            match   = cmd[pos:pos + len(keyword)]
            after   = cmd[pos + len(keyword):]
            highlighted = (
                f"{COLORS.TEXT}{before}"
                f"{COLORS.WARNING}{COLORS.BOLD}{match}{COLORS.RESET}"
                f"{COLORS.TEXT}{after}"
            )
        else:
            highlighted = f"{COLORS.TEXT}{cmd}"

        print(f"  {COLORS.DIM}{index:>4}  {highlighted}{COLORS.RESET}")

    print(f"\n  {COLORS.SUCCESS}  {len(matches)} match(es) found.{COLORS.RESET}\n")