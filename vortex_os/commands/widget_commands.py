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
    Shows and raises the VORTEX desktop window.

    Uses the signal-based request so it is safe to call
    from the terminal thread (QThread).
    Never calls .show() directly — that would be a
    cross-thread Qt violation and causes freezes.
    """
    from core.app_manager import get_app_manager
    manager = get_app_manager()

    if manager is None:
        print(f"\n{COLORS.ERROR}  [!] App manager not available."
              f"{COLORS.RESET}\n")
        return

    # Emit signal — main thread handles the actual .show() call
    manager.request_show_desktop()

    print(f"\n{COLORS.SUCCESS}  ◈ Desktop requested.{COLORS.RESET}")
    print(f"  {COLORS.DIM}If it doesn't appear, press F11 or "
          f"check your display.{COLORS.RESET}\n")

@with_timestamp
def cmd_monitor(args, config):
    """
    Command: monitor
    Opens the floating system monitor widget.
    """
    print(f"\n{COLORS.ACCENT}  ◈ Launching System Monitor...{COLORS.RESET}\n")
    _request_widget("monitor")

@with_timestamp
def cmd_newtab(args, config):
    """
    Command: newtab
    Opens a new tab in the VORTEX desktop terminal.
    The desktop terminal must be visible for this to work.
    """
    from core.app_manager import get_app_manager
    manager = get_app_manager()

    if manager is None or manager._desktop is None:
        print(f"\n{COLORS.ERROR}  [!] Desktop not available."
              f"{COLORS.RESET}\n")
        return

    # Use signal to be thread-safe
    # We reuse desktop_show_requested to show the desktop first,
    # then add a tab via a queued call
    from PyQt6.QtCore import QTimer

    def _do_newtab():
        desktop = manager._desktop
        if not desktop.isVisible():
            desktop.show()
        desktop.terminal.show()
        desktop.terminal.add_tab()
        desktop.terminal.raise_()

    # Schedule on main thread
    manager.desktop_show_requested.emit()
    QTimer.singleShot(300, _do_newtab)

    print(f"\n{COLORS.SUCCESS}  ◈ New tab requested.{COLORS.RESET}\n")    

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