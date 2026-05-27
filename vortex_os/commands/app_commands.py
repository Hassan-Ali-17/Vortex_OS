# commands/app_commands.py
# VORTEX OS - App system terminal commands

from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


def _get_registry():
    from apps.registry import get_registry
    return get_registry()


def _launch_on_main_thread(app_id):
    """
    Requests the main thread to launch an app.
    Thread-safe via AppManager signal.
    """
    from core.app_manager import get_app_manager
    manager = get_app_manager()
    if manager:
        manager.app_launch_requested.emit(app_id)
        return True
    return False


@with_timestamp
def cmd_app(args, config):
    """
    Command: app [subcommand] [id]

    app list              → list all installed apps
    app launch <id>       → launch an app
    app info <id>         → show app details
    app install <path>    → register app from folder
    app uninstall <id>    → remove app from registry
    """
    if not args or args[0].lower() == "list":
        _app_list()
        return

    sub = args[0].lower()

    if sub == "launch":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: app launch <id>{COLORS.RESET}\n")
            return
        _app_launch(args[1])

    elif sub == "info":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: app info <id>{COLORS.RESET}\n")
            return
        _app_info(args[1])

    elif sub == "install":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: app install <path>{COLORS.RESET}\n")
            return
        _app_install(args[1])

    elif sub == "uninstall":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: app uninstall <id>{COLORS.RESET}\n")
            return
        _app_uninstall(args[1])

    else:
        # Try to treat the arg as an app id directly
        _app_launch(args[0])


def _app_list():
    registry = _get_registry()
    apps     = registry.get_all()

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VORTEX APP REGISTRY{COLORS.RESET}\n")

    if not apps:
        print(f"  {COLORS.DIM}No apps installed.{COLORS.RESET}\n")
        return

    categories = {}
    for app in apps:
        cat = app.get("category", "misc")
        categories.setdefault(cat, []).append(app)

    for cat, cat_apps in sorted(categories.items()):
        print(f"  {COLORS.DIM}── {cat.upper()} ──{COLORS.RESET}")
        for app in cat_apps:
            running = registry.is_running(app["id"])
            marker  = (f"{COLORS.SUCCESS}●{COLORS.RESET}"
                       if running else
                       f"{COLORS.DIM}○{COLORS.RESET}")
            icon    = app.get("icon", "◈")
            print(
                f"  {marker} {icon}  "
                f"{COLORS.PRIMARY}{app['id']:<18}"
                f"{COLORS.TEXT}{app['name']:<20}"
                f"{COLORS.DIM}v{app['version']}"
            )
        print()

    print(f"  {COLORS.DIM}Usage: app launch <id>{COLORS.RESET}\n")


def _app_launch(app_id):
    """Requests app launch on main thread via signal."""
    from apps.registry import get_registry
    registry = get_registry()

    # Validate the app exists before emitting signal
    manifest = registry.get(app_id)
    if manifest is None:
        print(f"\n{COLORS.ERROR}  [!] App not found: '{app_id}'"
              f"{COLORS.RESET}")
        print(f"  {COLORS.DIM}Type 'app list' to see "
              f"available apps.{COLORS.RESET}\n")
        return

    print(f"\n{COLORS.ACCENT}  ◈ Launching: "
          f"{manifest.get('name', app_id)}{COLORS.RESET}")
    print(f"  {COLORS.DIM}{manifest.get('description', '')}"
          f"{COLORS.RESET}\n")

    success = _launch_on_main_thread(app_id)
    if not success:
        print(f"  {COLORS.ERROR}[!] App manager not available."
              f"{COLORS.RESET}\n")


def _app_info(app_id):
    registry = _get_registry()
    manifest = registry.get(app_id)

    if manifest is None:
        print(f"\n{COLORS.ERROR}  [!] App not found: '{app_id}'{COLORS.RESET}\n")
        return

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ APP INFO{COLORS.RESET}")
    fields = [
        ("ID",          manifest.get("id")),
        ("NAME",        manifest.get("name")),
        ("VERSION",     manifest.get("version")),
        ("DESCRIPTION", manifest.get("description")),
        ("CATEGORY",    manifest.get("category")),
        ("AUTHOR",      manifest.get("author")),
        ("PATH",        manifest.get("_path")),
    ]
    for label, value in fields:
        if value:
            print(f"  {COLORS.PRIMARY}{label:<14}{COLORS.TEXT}{value}")
    print()


def _app_install(path):
    registry        = _get_registry()
    success, result = registry.install(path)

    if success:
        print(f"\n{COLORS.SUCCESS}  ✓ App installed: {result}{COLORS.RESET}\n")
    else:
        print(f"\n{COLORS.ERROR}  [!] Install failed: {result}{COLORS.RESET}\n")


def _app_uninstall(app_id):
    registry        = _get_registry()
    success, result = registry.uninstall(app_id)

    if success:
        print(f"\n{COLORS.SUCCESS}  ✓ Uninstalled: {result}{COLORS.RESET}\n")
    else:
        print(f"\n{COLORS.ERROR}  [!] {result}{COLORS.RESET}\n")