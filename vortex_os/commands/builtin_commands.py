# commands/builtin_commands.py
# VORTEX OS - Built-in Command Definitions
# Each function = one command the user can type

import os
import platform
import datetime
import subprocess
import functools
import time


def with_timestamp(func):
    """
    Decorator that prints a timestamp after any command runs.
    
    Usage: add @with_timestamp above any command function.
    
    How decorators work:
        @with_timestamp
        def cmd_clock(...): ...
    
    Is exactly equivalent to:
        cmd_clock = with_timestamp(cmd_clock)
    
    So when cmd_clock is called, it actually calls the wrapper,
    which calls the real cmd_clock, then prints the timestamp.
    """
    @functools.wraps(func)   # Preserves the original function's name/docstring
    def wrapper(args, config):
        result = func(args, config)   # Run the actual command first
        
        # Print a subtle timestamp after the output
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{COLORS.DIM}  ─── executed at {ts} ───{COLORS.RESET}")
        
        return result   # Pass through any return value (like "EXIT")
    return wrapper

from themes.colors import COLORS

@with_timestamp
def cmd_help(args, config):
    """
    Command: help
    Now accepts an optional router reference via config.
    Falls back to static list if router not available.
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}{'='*52}")
    print(f"  {config['os_name']} v{config['version']} — COMMAND REFERENCE")
    print(f"{'='*52}{COLORS.RESET}")

    # If router was injected into config, use live registry
    router = config.get("_router")
    if router:
        commands = router.get_all_commands()
    else:
        # Fallback static list
        commands = [
            ("apps",    "List VORTEX applications"),
            ("clear",   "Clear the terminal screen"),
            ("clock",   "Show time | clock live for live mode"),
            ("exit",    "Exit VORTEX terminal"),
            ("help",    "Show this help menu"),
            ("ignite",  "Power control"),
            ("open",    "Launch apps or URLs"),
            ("scan",    "System & network scanner"),
            ("system",  "Show system hardware info"),
            ("vault",   "Filesystem explorer"),
            ("version", "Show VORTEX OS version"),
            ("whoami",  "Show current user identity"),
        ]

    for cmd, desc in commands:
        print(f"  {COLORS.PRIMARY}{cmd:<14}{COLORS.TEXT}{desc}")

    print(f"\n{COLORS.DIM}  Aliases: q=exit  h=help  cls=clear  ls=vault list  me=whoami{COLORS.RESET}\n")

@with_timestamp
def cmd_clock(args, config):
    """
    Command: clock
    
    Without arguments : shows current date/time once
    With 'live' arg   : enters live ticking mode (Ctrl+C to exit)
    
    Example:
        clock         ← static
        clock live    ← ticking
    """
    # Check if user typed 'clock live'
    live_mode = len(args) > 0 and args[0].lower() == "live"

    if not live_mode:
        # Static output — just show once
        _print_clock_face(config)
        return

    # Live ticking mode
    print(f"{COLORS.DIM}  Live clock active. Press Ctrl+C to return to shell.{COLORS.RESET}\n")
    time.sleep(0.8)

    try:
        while True:
            os.system('clear')   # Wipe screen each tick

            # Reprint banner so it doesn't feel naked
            print(f"\n{COLORS.PRIMARY}{COLORS.BOLD}  ◈ VORTEX LIVE CLOCK{COLORS.RESET}")
            print(f"  {COLORS.DIM}Press Ctrl+C to exit{COLORS.RESET}\n")

            _print_clock_face(config)

            time.sleep(1)   # Wait 1 second before next tick

    except KeyboardInterrupt:
        # User pressed Ctrl+C — clean exit back to shell
        os.system('clear')
        print(f"\n{COLORS.WARNING}  Clock stopped. Returning to shell...{COLORS.RESET}\n")


def _print_clock_face(config):
    """
    Helper — prints the formatted clock face.
    Extracted so both static and live modes share the same display code.
    This is the DRY principle: Don't Repeat Yourself.
    """
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %d %B %Y").upper()
    time_str = now.strftime("%H:%M:%S")
    week_num = now.strftime("%V")   # ISO week number

    print(f"  {COLORS.PRIMARY}DATE   : {COLORS.TEXT}{date_str}")
    print(f"  {COLORS.PRIMARY}TIME   : {COLORS.SUCCESS}{COLORS.BOLD}{time_str}{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}WEEK   : {COLORS.TEXT}Week {week_num}")
    print(f"  {COLORS.PRIMARY}UNIX   : {COLORS.DIM}{int(time.time())}{COLORS.RESET}")
    print()

@with_timestamp
def cmd_whoami(args, config):
    """
    Command: whoami
    Displays current Linux user identity and environment details.
    Uses os.getenv() to read environment variables safely.
    """
    import grp  # Built-in module for reading Unix groups

    username = os.getenv('USER') or os.getenv('LOGNAME') or 'unknown'
    home_dir = os.path.expanduser('~')
    shell    = os.getenv('SHELL', 'unknown')
    term     = os.getenv('TERM', 'unknown')

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ USER IDENTITY{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}USER     : {COLORS.TEXT}{username}")
    print(f"  {COLORS.PRIMARY}HOME     : {COLORS.TEXT}{home_dir}")
    print(f"  {COLORS.PRIMARY}SHELL    : {COLORS.TEXT}{shell}")
    print(f"  {COLORS.PRIMARY}TERMINAL : {COLORS.TEXT}{term}")

    # Get Unix groups for the current user
    try:
        groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
        # Limit display to first 6 groups — some users have many
        groups_display = ', '.join(groups[:6])
        if len(groups) > 6:
            groups_display += f" (+{len(groups)-6} more)"
        print(f"  {COLORS.PRIMARY}GROUPS   : {COLORS.TEXT}{groups_display or 'none'}")
    except Exception:
        print(f"  {COLORS.PRIMARY}GROUPS   : {COLORS.WARNING}unavailable")

    print()    
def cmd_clear(args, config):
    """
    Command: clear
    Clears the terminal screen.
    Works on Linux/Mac (clear) and Windows (cls).
    """
    os.system('clear' if os.name != 'nt' else 'cls')

@with_timestamp
def cmd_system(args, config):
    """
    Command: system
    Displays system hardware and OS information.
    Uses Python's 'platform' module (built-in, no install needed).
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ SYSTEM INTEL{COLORS.RESET}")

    # platform.system() → 'Linux'
    print(f"  {COLORS.PRIMARY}OS       : {COLORS.TEXT}{platform.system()} {platform.release()}")
    
    # platform.node() → your computer's hostname
    print(f"  {COLORS.PRIMARY}HOST     : {COLORS.TEXT}{platform.node()}")
    
    # platform.processor() → CPU info
    print(f"  {COLORS.PRIMARY}CPU      : {COLORS.TEXT}{platform.processor() or 'Unknown'}")
    
    # platform.machine() → x86_64, arm64, etc.
    print(f"  {COLORS.PRIMARY}ARCH     : {COLORS.TEXT}{platform.machine()}")
    
    # Python version being used
    print(f"  {COLORS.PRIMARY}PYTHON   : {COLORS.TEXT}{platform.python_version()}")
    
    # VORTEX OS version from config
    print(f"  {COLORS.PRIMARY}VORTEX   : {COLORS.TEXT}v{config['version']} [{config['codename']}]")
    
    # Try to get RAM info using /proc/meminfo (Linux only)
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        # MemTotal is always the first line
        total_ram_kb  = int(lines[0].split()[1])
        avail_ram_kb  = int(lines[2].split()[1])
        
        total_ram_mb = total_ram_kb // 1024
        avail_ram_mb = avail_ram_kb // 1024
        
        print(f"  {COLORS.PRIMARY}RAM      : {COLORS.TEXT}{avail_ram_mb} MB free / {total_ram_mb} MB total")
    
    except FileNotFoundError:
        # /proc/meminfo doesn't exist on Windows/Mac
        print(f"  {COLORS.PRIMARY}RAM      : {COLORS.WARNING}Not available on this OS")

    print()
    
@with_timestamp
def cmd_version(args, config):
    """
    Command: version
    Displays the current VORTEX OS version details from config.
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VORTEX VERSION INFO{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}NAME     : {COLORS.TEXT}{config['os_name']}")
    print(f"  {COLORS.PRIMARY}VERSION  : {COLORS.SUCCESS}{COLORS.BOLD}v{config['version']}{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}CODENAME : {COLORS.TEXT}{config['codename']}")
    print(f"  {COLORS.PRIMARY}AUTHOR   : {COLORS.TEXT}{config['author']}")
    print()


def cmd_exit(args, config):
    """
    Command: exit
    Cleanly shuts down the VORTEX terminal.
    Returns a special signal string that the shell loop watches for.
    """
    print(f"\n{COLORS.WARNING}  ◈ VORTEX TERMINAL SHUTTING DOWN...{COLORS.RESET}")
    print(f"{COLORS.DIM}  Session ended. Stay in the grid.{COLORS.RESET}\n")
    
    # Returning "EXIT" tells the shell loop to stop
    return "EXIT"