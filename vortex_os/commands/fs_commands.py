# commands/fs_commands.py
# VORTEX OS - Filesystem Commands
# vx, landmark, and vx-aware vault enhancements

import os

from themes.colors      import COLORS
from core.filesystem    import get_vfs
from commands.builtin_commands import with_timestamp


# ─────────────────────────────────────────────
#  VX COMMAND — Virtual path navigator
#
#  vx                → show all vx locations
#  vx <name>         → navigate to vx://name
#  vx where          → show current location in vx format
#  vx resolve <name> → show real path for a vx name
# ─────────────────────────────────────────────

@with_timestamp
def cmd_vx(args, config):
    """
    Command: vx [name | where | resolve <name> | list]

    VORTEX virtual filesystem navigator.
    Navigate using VORTEX location names instead of raw paths.

    Examples:
        vx             → list all locations
        vx core        → go to vx://core
        vx home        → go to home directory
        vx where       → show current location as vx:// path
        vx resolve config → show real path of vx://config
    """
    vfs = get_vfs()

    # No args — show location map
    if not args:
        _vx_list(vfs)
        return

    subcommand = args[0].lower()

    if subcommand in ("list", "ls", "map"):
        _vx_list(vfs)

    elif subcommand == "where":
        _vx_where(vfs)

    elif subcommand == "resolve":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: vx resolve <name>{COLORS.RESET}\n")
            return
        _vx_resolve(vfs, args[1])

    else:
        # Treat as a navigation target
        _vx_navigate(vfs, subcommand)


def _vx_list(vfs):
    """
    Displays the full VORTEX location map in a table.
    Shows built-in locations and user landmarks separately.
    Also shows whether the real path currently exists.
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VORTEX FILESYSTEM MAP{COLORS.RESET}\n")

    locations = vfs.get_all_locations()

    current_real = os.getcwd()

    for name, real_path, kind in locations:

        # Does the real directory actually exist on disk?
        exists  = os.path.isdir(real_path)
        ex_mark = (f"{COLORS.SUCCESS}✓{COLORS.RESET}"
                   if exists else
                   f"{COLORS.ERROR}✗{COLORS.RESET}")

        # Is this the current directory?
        is_here = (os.path.normpath(real_path) ==
                   os.path.normpath(current_real))
        here_mark = f" {COLORS.WARNING}← here{COLORS.RESET}" if is_here else ""

        # Kind badge
        if kind == "landmark":
            badge = f"{COLORS.ACCENT}[landmark]{COLORS.RESET}"
        else:
            badge = f"{COLORS.DIM}[builtin] {COLORS.RESET}"

        # Compress home dir for display
        home = os.path.expanduser("~")
        display_real = real_path
        if display_real.startswith(home):
            display_real = "~" + display_real[len(home):]

        print(f"  {ex_mark} {COLORS.PRIMARY}vx://{name:<12}{COLORS.RESET}"
              f"  {badge}  "
              f"{COLORS.TEXT}{display_real}{here_mark}")

    print(f"\n  {COLORS.DIM}Usage: vx <name>   "
          f"Add landmark: landmark save <name>{COLORS.RESET}\n")


def _vx_where(vfs):
    """Shows the current directory as a vx:// path."""
    real    = os.getcwd()
    display = vfs.display_path(real)

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ CURRENT LOCATION{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}VX PATH  : {COLORS.TEXT}{display}")
    print(f"  {COLORS.PRIMARY}REAL PATH: {COLORS.DIM}{real}{COLORS.RESET}\n")


def _vx_resolve(vfs, name):
    """Shows what a vx:// name resolves to."""
    real = vfs.resolve(name)

    print(f"\n{COLORS.ACCENT}  ◈ RESOLVE: vx://{name}{COLORS.RESET}")

    if real is None:
        print(f"  {COLORS.ERROR}[!] Unknown location: '{name}'{COLORS.RESET}\n")
        return

    exists = os.path.isdir(real)
    status = (f"{COLORS.SUCCESS}exists{COLORS.RESET}"
              if exists else
              f"{COLORS.ERROR}not found on disk{COLORS.RESET}")

    print(f"  {COLORS.PRIMARY}REAL PATH : {COLORS.TEXT}{real}")
    print(f"  {COLORS.PRIMARY}STATUS    : {status}\n")


def _vx_navigate(vfs, target):
    """
    Changes the current directory to the resolved vx path.

    After navigating, shows the new location in vx:// format.
    The shell prompt will also update automatically since it
    reads os.getcwd() on every input.
    """
    real = vfs.resolve(target)

    if real is None:
        print(f"\n{COLORS.ERROR}  [!] Unknown location: "
              f"'{target}'{COLORS.RESET}")
        print(f"  {COLORS.DIM}Type 'vx' to see available "
              f"locations.{COLORS.RESET}\n")
        return

    if not os.path.isdir(real):
        print(f"\n{COLORS.ERROR}  [!] Path does not exist: "
              f"{real}{COLORS.RESET}\n")
        return

    os.chdir(real)
    display = vfs.display_path(real)

    print(f"\n{COLORS.SUCCESS}  ✓ Navigated to: "
          f"{COLORS.BOLD}{display}{COLORS.RESET}")
    print(f"  {COLORS.DIM}{real}{COLORS.RESET}\n")


# ─────────────────────────────────────────────
#  LANDMARK COMMAND — Save named locations
#
#  landmark             → list all landmarks
#  landmark save <name> → save CWD as vx://<name>
#  landmark save <name> <path> → save specific path
#  landmark remove <name> → delete a landmark
#  landmark go <name>   → navigate to landmark
# ─────────────────────────────────────────────

@with_timestamp
def cmd_landmark(args, config):
    """
    Command: landmark [save|remove|go|list] [name] [path]

    Manage user-defined VORTEX filesystem landmarks.

    Examples:
        landmark                    → list all landmarks
        landmark save projects      → save CWD as vx://projects
        landmark save work ~/work   → save ~/work as vx://work
        landmark remove projects    → delete vx://projects
        landmark go projects        → navigate to vx://projects
    """
    vfs = get_vfs()

    if not args or args[0].lower() in ("list", "ls"):
        _landmark_list(vfs)
        return

    subcommand = args[0].lower()

    if subcommand == "save":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: "
                  f"landmark save <name> [path]{COLORS.RESET}\n")
            return
        name      = args[1].lower()
        real_path = args[2] if len(args) > 2 else None
        _landmark_save(vfs, name, real_path)

    elif subcommand in ("remove", "rm", "delete", "del"):
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: "
                  f"landmark remove <name>{COLORS.RESET}\n")
            return
        _landmark_remove(vfs, args[1].lower())

    elif subcommand in ("go", "navigate", "cd"):
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: "
                  f"landmark go <name>{COLORS.RESET}\n")
            return
        # Reuse vx navigation since landmarks are resolved the same way
        _vx_navigate(vfs, args[1].lower())

    else:
        print(f"{COLORS.ERROR}  [!] Unknown subcommand: "
              f"'{subcommand}'{COLORS.RESET}")
        print(f"  {COLORS.DIM}Options: save | remove | go | list"
              f"{COLORS.RESET}\n")


def _landmark_list(vfs):
    """Lists only user landmarks (not built-in locations)."""
    locations = vfs.get_all_locations()
    landmarks = [(n, p) for n, p, k in locations if k == "landmark"]

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ USER LANDMARKS{COLORS.RESET}\n")

    if not landmarks:
        print(f"  {COLORS.DIM}No landmarks saved yet.")
        print(f"  Use 'landmark save <name>' to create one.{COLORS.RESET}\n")
        return

    home = os.path.expanduser("~")

    for name, real_path in landmarks:
        exists   = os.path.isdir(real_path)
        ex_color = COLORS.SUCCESS if exists else COLORS.ERROR
        ex_mark  = "✓" if exists else "✗"

        display = real_path
        if display.startswith(home):
            display = "~" + display[len(home):]

        print(f"  {ex_color}{ex_mark}{COLORS.RESET}  "
              f"{COLORS.PRIMARY}vx://{name:<16}"
              f"{COLORS.TEXT}{display}")

    print()


def _landmark_save(vfs, name, real_path):
    """Saves a landmark and reports result."""
    success, result = vfs.add_landmark(name, real_path)

    if success:
        home    = os.path.expanduser("~")
        display = result
        if display.startswith(home):
            display = "~" + display[len(home):]

        print(f"\n{COLORS.SUCCESS}  ✓ Landmark saved:{COLORS.RESET}")
        print(f"  {COLORS.PRIMARY}vx://{name}{COLORS.RESET}  "
              f"→  {COLORS.TEXT}{display}\n")
    else:
        print(f"\n{COLORS.ERROR}  [!] Could not save landmark: "
              f"{result}{COLORS.RESET}\n")


def _landmark_remove(vfs, name):
    """Removes a landmark and reports result."""
    success, result = vfs.remove_landmark(name)

    if success:
        print(f"\n{COLORS.SUCCESS}  ✓ Landmark removed: "
              f"vx://{result}{COLORS.RESET}\n")
    else:
        print(f"\n{COLORS.ERROR}  [!] {result}{COLORS.RESET}\n")


# ─────────────────────────────────────────────
#  VX-AWARE VAULT OVERRIDE
#
#  Updates vault list/go/info/find to understand
#  vx:// paths in addition to real paths.
# ─────────────────────────────────────────────

@with_timestamp
def cmd_vault_vx(args, config):
    """
    Command: vault [subcommand] [path]

    Phase 7 upgrade: vault now understands vx:// paths.

    Examples:
        vault list vx://config   → list the config directory
        vault go vx://core       → navigate to project root
        vault info vx://vault    → info about vault_storage
        vault find py vx://core  → search in vx://core
    """
    from commands.system_commands import (
        _vault_list, _vault_go,
        _vault_info, _vault_find
    )

    vfs = get_vfs()

    def resolve_arg(raw):
        """
        Resolves a path argument — handles both vx:// and real paths.
        Returns the real path string.
        """
        if raw is None:
            return None
        if raw.startswith("vx://") or vfs.resolve(raw) is not None:
            return vfs.resolve(raw) or raw
        return raw

    # No args — list current directory
    if not args:
        _vault_list(os.getcwd())
        return

    subcommand = args[0].lower()
    raw_target = args[1] if len(args) > 1 else None
    target     = resolve_arg(raw_target)

    if subcommand in ("list", "ls"):
        path = target or os.getcwd()
        _vault_list(path)

    elif subcommand in ("go", "cd", "navigate"):
        if not target:
            print(f"{COLORS.ERROR}  [!] Usage: vault go <path>{COLORS.RESET}\n")
            return
        _vault_go(target)

    elif subcommand == "info":
        path = target or os.getcwd()
        _vault_info(path)

    elif subcommand == "find":
        if not raw_target:
            print(f"{COLORS.ERROR}  [!] Usage: vault find <name> "
                  f"[path]{COLORS.RESET}\n")
            return
        # Third arg is the search root (optional)
        raw_root   = args[2] if len(args) > 2 else None
        search_root = resolve_arg(raw_root)
        _vault_find(raw_target, search_root)

    else:
        print(f"{COLORS.ERROR}  [!] Unknown vault subcommand: "
              f"'{subcommand}'{COLORS.RESET}")
        print(f"  {COLORS.DIM}Usage: vault | vault list [path] | "
              f"vault go <path> | vault info <path> | "
              f"vault find <name> [path]{COLORS.RESET}\n")