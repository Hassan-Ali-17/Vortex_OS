# commands/widget_commands.py
# VORTEX OS - Widget launch commands (Phase 4 fix)
# Uses AppManager signals instead of raw threads.

from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


def _request_widget(name):
    """
    Asks the AppManager (main thread) to open a widget.
    Safe to call from the terminal thread.
    """
    from core.app_manager import get_app_manager
    manager = get_app_manager()

    if manager is None:
        print(f"{COLORS.ERROR}  [!] GUI manager not available.{COLORS.RESET}\n")
        return False

    manager.request_widget(name)
    return True


@with_timestamp
def cmd_clock_gui(args, config):
    """
    Command: clock gui
    Opens the floating clock widget.
    Without 'gui' arg, prints terminal clock instead.
    """
    if not args or args[0].lower() not in ("--gui", "gui", "-g"):
        from commands.builtin_commands import _print_clock_face
        _print_clock_face(config)
        return

    print(f"\n{COLORS.ACCENT}  ◈ Launching Clock Widget...{COLORS.RESET}")
    print(f"  {COLORS.DIM}Floating window will appear on your desktop.{COLORS.RESET}")
    print(f"  {COLORS.DIM}Press ESC on the widget to close it.{COLORS.RESET}\n")
    _request_widget("clock")


@with_timestamp
def cmd_calendar(args, config):
    """
    Command: calendar
    Opens the floating calendar widget.
    """
    print(f"\n{COLORS.ACCENT}  ◈ Launching Calendar Widget...{COLORS.RESET}")
    print(f"  {COLORS.DIM}Floating window will appear on your desktop.{COLORS.RESET}")
    print(f"  {COLORS.DIM}Press ESC on the widget to close it.{COLORS.RESET}\n")
    _request_widget("calendar")
    

@with_timestamp
def cmd_desktop(args, config):
    """
    Command: desktop
    Opens or raises the VORTEX desktop window.
    """
    from core.app_manager import get_app_manager
    manager = get_app_manager()
    if manager and hasattr(manager, '_desktop'):
        manager._desktop.show()
        manager._desktop.raise_()
        print(f"\n{COLORS.SUCCESS}  ◈ Desktop raised.{COLORS.RESET}\n")
    else:
        print(f"\n{COLORS.ERROR}  [!] Desktop not available.{COLORS.RESET}\n")


@with_timestamp
def cmd_widgets(args, config):
    """
    Command: widgets
    Lists all available widgets and their status.
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VORTEX WIDGET REGISTRY{COLORS.RESET}\n")

    widget_list = [
        ("Clock",    "clock gui",  "ACTIVE",  "Live clock with seconds arc"),
        ("Calendar", "calendar",   "ACTIVE",  "Month calendar, navigate months"),
        ("Monitor",  "monitor",    "PLANNED", "System resource monitor (Phase 6)"),
        ("Launcher", "launcher",   "PLANNED", "App launcher (Phase 6)"),
        ("Notes",    "notes",      "PLANNED", "Sticky notes (Phase 9)"),
    ]

    for name, cmd, status, desc in widget_list:
        if status == "ACTIVE":
            marker    = f"{COLORS.SUCCESS}●{COLORS.RESET}"
            cmd_color = COLORS.PRIMARY
        else:
            marker    = f"{COLORS.DIM}○{COLORS.RESET}"
            cmd_color = COLORS.DIM

        print(f"  {marker} {COLORS.TEXT}{name:<12}"
              f"{cmd_color}{cmd:<16}{COLORS.RESET}"
              f"{COLORS.DIM}{desc}")
    print()