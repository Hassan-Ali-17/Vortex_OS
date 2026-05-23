# commands/system_commands.py
# VORTEX OS - Phase 2 System Commands
# New commands: vault, scan, apps, ignite, open

import os
import sys
import subprocess
import datetime
import shutil

from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


# ─────────────────────────────────────────────
#  VAULT COMMAND
#  A filesystem browser / navigator.
#  'vault' alone → list current directory
#  'vault list <path>' → list that path
#  'vault go <path>'   → change directory
#  'vault info <path>' → file/folder details
# ─────────────────────────────────────────────

@with_timestamp
def cmd_vault(args, config):
    if not args:
        _vault_list(os.getcwd())
        return

    subcommand = args[0].lower()
    target = args[1] if len(args) > 1 else None

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

    elif subcommand == "find":          # ← ADD THIS BLOCK
        if not target:
            print(f"{COLORS.ERROR}  [!] Usage: vault find <name>{COLORS.RESET}\n")
            print(f"{COLORS.DIM}  Example: vault find python{COLORS.RESET}\n")
            return
        # Optional third argument = start path
        start = args[2] if len(args) > 2 else None
        _vault_find(target, start)

    else:
        print(f"{COLORS.ERROR}  [!] Unknown vault subcommand: '{subcommand}'{COLORS.RESET}")
        print(f"{COLORS.DIM}  Usage: vault | vault list | vault go <path> "
              f"| vault info <path> | vault find <name>{COLORS.RESET}\n")

def _vault_list(path):
    """Lists directory contents with type indicators and sizes."""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"{COLORS.ERROR}  [!] Path not found: {path}{COLORS.RESET}\n")
        return

    if not os.path.isdir(path):
        print(f"{COLORS.ERROR}  [!] Not a directory: {path}{COLORS.RESET}\n")
        return

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VAULT — {path}{COLORS.RESET}")

    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        print(f"{COLORS.ERROR}  [!] Permission denied: {path}{COLORS.RESET}\n")
        return

    if not entries:
        print(f"  {COLORS.DIM}  (empty directory){COLORS.RESET}\n")
        return

    dirs  = [e for e in entries if os.path.isdir(os.path.join(path, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(path, e))]

    # Print directories first
    for d in dirs:
        print(f"  {COLORS.PRIMARY}  ▸ DIR   {COLORS.TEXT}{d}/")

    # Then files with size
    for f in files:
        full_path = os.path.join(path, f)
        size = os.path.getsize(full_path)
        size_str = _format_size(size)
        print(f"  {COLORS.SUCCESS}  · FILE  {COLORS.TEXT}{f:<35}{COLORS.DIM}{size_str}")

    print(f"\n  {COLORS.DIM}{len(dirs)} dirs, {len(files)} files{COLORS.RESET}\n")


def _vault_go(path):
    """Changes current working directory."""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"{COLORS.ERROR}  [!] Path not found: {path}{COLORS.RESET}\n")
        return

    if not os.path.isdir(path):
        print(f"{COLORS.ERROR}  [!] Not a directory: {path}{COLORS.RESET}\n")
        return

    os.chdir(path)
    print(f"{COLORS.SUCCESS}  ✓ Navigated to: {path}{COLORS.RESET}\n")


def _vault_info(path):
    """Shows detailed info about a file or directory."""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"{COLORS.ERROR}  [!] Path not found: {path}{COLORS.RESET}\n")
        return

    stat = os.stat(path)
    is_dir = os.path.isdir(path)

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VAULT INFO{COLORS.RESET}")
    print(f"  {COLORS.PRIMARY}PATH     : {COLORS.TEXT}{os.path.abspath(path)}")
    print(f"  {COLORS.PRIMARY}TYPE     : {COLORS.TEXT}{'Directory' if is_dir else 'File'}")
    print(f"  {COLORS.PRIMARY}SIZE     : {COLORS.TEXT}{_format_size(stat.st_size)}")

    mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
    print(f"  {COLORS.PRIMARY}MODIFIED : {COLORS.TEXT}{mtime.strftime('%Y-%m-%d %H:%M:%S')}")

    # Octal permissions like 755, 644
    permissions = oct(stat.st_mode)[-3:]
    print(f"  {COLORS.PRIMARY}PERMS    : {COLORS.TEXT}{permissions}")
    print()


def _vault_find(name_pattern, start_path=None):
    """
    Recursively searches for files and folders matching name_pattern.
    
    Args:
        name_pattern : string to search for (case-insensitive, partial match)
        start_path   : where to start searching (default: current directory)
    
    Why case-insensitive partial match?
    Because 'find pyth' should find 'python3', 'Python.cfg', 'mypython.py'.
    Real tools like 'find' and 'locate' work the same way.
    """
    if start_path is None:
        start_path = os.getcwd()

    start_path = os.path.expanduser(start_path)

    if not os.path.exists(start_path):
        print(f"{COLORS.ERROR}  [!] Start path not found: {start_path}{COLORS.RESET}\n")
        return

    pattern = name_pattern.lower()

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VAULT FIND — '{name_pattern}'{COLORS.RESET}")
    print(f"  {COLORS.DIM}Searching in: {start_path}{COLORS.RESET}\n")

    found_count = 0
    scanned_dirs = 0

    try:
        for root, dirs, files in os.walk(start_path):
            scanned_dirs += 1

            # Skip hidden directories (e.g. .git, .cache) — they slow
            # down the search and rarely contain what users want
            # We modify 'dirs' IN PLACE — os.walk respects this
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            # Check directory names
            for d in dirs:
                if pattern in d.lower():
                    full_path = os.path.join(root, d)
                    print(f"  {COLORS.PRIMARY}  ▸ DIR   {COLORS.TEXT}{full_path}")
                    found_count += 1

            # Check file names
            for f in files:
                if pattern in f.lower():
                    full_path = os.path.join(root, f)
                    size = _format_size(os.path.getsize(full_path))
                    print(f"  {COLORS.SUCCESS}  · FILE  {COLORS.TEXT}{full_path:<55}{COLORS.DIM}{size}")
                    found_count += 1

            # Safety limit — don't scan 10,000 dirs silently
            if scanned_dirs > 500:
                print(f"\n  {COLORS.WARNING}  [!] Scan limit reached (500 dirs). "
                      f"Specify a narrower start path.{COLORS.RESET}")
                break

    except KeyboardInterrupt:
        print(f"\n{COLORS.WARNING}  Search interrupted by user.{COLORS.RESET}")

    # Summary line
    if found_count == 0:
        print(f"  {COLORS.DIM}No matches found for '{name_pattern}'{COLORS.RESET}")
    else:
        print(f"\n  {COLORS.SUCCESS}  {found_count} match(es) found "
              f"in {scanned_dirs} directories scanned.{COLORS.RESET}")
    print()


def _format_size(size_bytes):
    """Converts raw bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.2f} GB"


# ─────────────────────────────────────────────
#  SCAN COMMAND
#  Network + system scanner
#  'scan'          → basic system health check
#  'scan ports'    → show open ports (uses ss)
#  'scan network'  → show network interfaces
#  'scan disk'     → show disk usage
# ─────────────────────────────────────────────

@with_timestamp
def cmd_scan(args, config):
    """
    Command: scan [target]
    System and network scanning utility.
    """
    target = args[0].lower() if args else "health"

    if target == "health":
        _scan_health()
    elif target in ("ports", "port"):
        _scan_ports()
    elif target in ("network", "net"):
        _scan_network()
    elif target in ("disk", "storage"):
        _scan_disk()
    else:
        print(f"{COLORS.ERROR}  [!] Unknown scan target: '{target}'{COLORS.RESET}")
        print(f"{COLORS.DIM}  Options: scan | scan ports | scan network | scan disk{COLORS.RESET}\n")


def _scan_health():
    """Quick system health overview."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ SYSTEM HEALTH SCAN{COLORS.RESET}")

    # Uptime
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_secs = float(f.read().split()[0])
        hours   = int(uptime_secs // 3600)
        minutes = int((uptime_secs % 3600) // 60)
        print(f"  {COLORS.PRIMARY}UPTIME   : {COLORS.TEXT}{hours}h {minutes}m")
    except Exception:
        print(f"  {COLORS.PRIMARY}UPTIME   : {COLORS.WARNING}unavailable")

    # Load average
    try:
        load = os.getloadavg()
        print(f"  {COLORS.PRIMARY}LOAD     : {COLORS.TEXT}{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}  (1m/5m/15m)")
    except Exception:
        print(f"  {COLORS.PRIMARY}LOAD     : {COLORS.WARNING}unavailable")

    # RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total = int(lines[0].split()[1]) // 1024
        free  = int(lines[2].split()[1]) // 1024
        used  = total - free
        pct   = (used / total) * 100
        bar   = _make_bar(pct)
        print(f"  {COLORS.PRIMARY}RAM      : {COLORS.TEXT}{bar} {used}MB / {total}MB ({pct:.0f}%)")
    except Exception:
        print(f"  {COLORS.PRIMARY}RAM      : {COLORS.WARNING}unavailable")

    # Disk
    try:
        total, used, free = shutil.disk_usage("/")
        pct = (used / total) * 100
        bar = _make_bar(pct)
        print(f"  {COLORS.PRIMARY}DISK /   : {COLORS.TEXT}{bar} {used//1024**3}GB / {total//1024**3}GB ({pct:.0f}%)")
    except Exception:
        print(f"  {COLORS.PRIMARY}DISK     : {COLORS.WARNING}unavailable")

    print()


def _make_bar(percentage, width=20):
    """Creates a text progress bar. e.g. [████████░░░░] 40%"""
    filled = int((percentage / 100) * width)
    bar    = '█' * filled + '░' * (width - filled)
    
    if percentage > 85:
        color = COLORS.ERROR
    elif percentage > 60:
        color = COLORS.WARNING
    else:
        color = COLORS.SUCCESS

    return f"{color}[{bar}]{COLORS.RESET}"


def _scan_ports():
    """Lists listening ports using the 'ss' command."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ OPEN PORTS SCAN{COLORS.RESET}")
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],          # TCP, listening, numeric, processes
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[:15]:   # Limit to 15 lines
                print(f"  {COLORS.DIM}{line}")
        else:
            print(f"  {COLORS.DIM}No listening ports found.")
    except FileNotFoundError:
        print(f"  {COLORS.WARNING}  'ss' command not found. Install: sudo apt install iproute2")
    except subprocess.TimeoutExpired:
        print(f"  {COLORS.ERROR}  Scan timed out.")
    print()


def _scan_network():
    """Shows network interfaces using 'ip addr'."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ NETWORK INTERFACES{COLORS.RESET}")
    try:
        result = subprocess.run(
            ["ip", "-brief", "addr"],  # Compact format
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"  {COLORS.TEXT}{line}")
    except FileNotFoundError:
        print(f"  {COLORS.WARNING}  'ip' command not found.")
    print()


def _scan_disk():
    """Shows disk usage using 'df'."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ DISK USAGE{COLORS.RESET}")
    try:
        result = subprocess.run(
            ["df", "-h", "--output=source,size,used,avail,pcent,target"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            # Header
            print(f"  {COLORS.PRIMARY}{lines[0]}")
            for line in lines[1:]:
                print(f"  {COLORS.TEXT}{line}")
    except FileNotFoundError:
        print(f"  {COLORS.WARNING}  'df' command not found.")
    print()


# ─────────────────────────────────────────────
#  APPS COMMAND
#  Lists installed / available VORTEX apps.
#  Phase 2 = static list. Phase 9 = dynamic.
# ─────────────────────────────────────────────

@with_timestamp
def cmd_apps(args, config):
    """
    Command: apps
    Lists available VORTEX OS applications.
    In Phase 2 this is a static list.
    Phase 9 will make this dynamic.
    """
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ VORTEX APP REGISTRY{COLORS.RESET}")

    # Static app list for Phase 2
    # Format: (name, status, description)
    apps = [
        ("Terminal",     "ACTIVE",   "VORTEX command shell"),
        ("Vault",        "ACTIVE",   "Filesystem explorer"),
        ("Scanner",      "ACTIVE",   "System & network scanner"),
        ("Clock",        "ACTIVE",   "Time & date widget"),
        ("Desktop",      "PLANNED",  "PyQt6 desktop environment (Phase 5)"),
        ("File Manager", "PLANNED",  "GUI file explorer (Phase 9)"),
        ("AI Assistant", "PLANNED",  "Integrated AI (Phase 12)"),
        ("Voice Agent",  "PLANNED",  "Voice commands (Phase 13)"),
    ]

    for name, status, desc in apps:
        if status == "ACTIVE":
            status_color = COLORS.SUCCESS
            marker = "●"
        else:
            status_color = COLORS.DIM
            marker = "○"

        print(f"  {status_color}{marker} {name:<16}{COLORS.DIM}{status:<10}{COLORS.TEXT}{desc}")

    print()


# ─────────────────────────────────────────────
#  IGNITE COMMAND
#  System boot / reboot / shutdown controls.
#  Safety-locked: requires confirmation.
# ─────────────────────────────────────────────

@with_timestamp
def cmd_ignite(args, config):
    """
    Command: ignite [action]
    Power management for VORTEX OS.
    
    Usage:
        ignite           → shows power menu
        ignite restart   → restarts terminal shell
        ignite shutdown  → shuts down the system (with confirmation)
        ignite reboot    → reboots the system (with confirmation)
    """
    action = args[0].lower() if args else None

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ IGNITE — POWER CONTROL{COLORS.RESET}")

    if action is None:
        # Show power menu
        print(f"  {COLORS.PRIMARY}restart  {COLORS.TEXT}: Restart the VORTEX terminal")
        print(f"  {COLORS.PRIMARY}shutdown {COLORS.TEXT}: Power off the system")
        print(f"  {COLORS.PRIMARY}reboot   {COLORS.TEXT}: Reboot the system")
        print(f"\n  {COLORS.DIM}Usage: ignite <action>{COLORS.RESET}\n")
        return

    if action == "restart":
        print(f"{COLORS.WARNING}  ◈ Restarting VORTEX terminal...{COLORS.RESET}")
        import time
        time.sleep(1)
        # Re-execute the current Python process
        os.execv(sys.executable, [sys.executable] + sys.argv)

    elif action in ("shutdown", "reboot"):
        verb = "shut down" if action == "shutdown" else "reboot"
        confirm = input(f"\n{COLORS.WARNING}  [?] Confirm {verb}? (yes/no): {COLORS.RESET}").strip().lower()

        if confirm in ("yes", "y"):
            print(f"{COLORS.ERROR}  ◈ Initiating {action}...{COLORS.RESET}\n")
            cmd = "shutdown -h now" if action == "shutdown" else "reboot"
            try:
                subprocess.run(cmd.split(), check=True)
            except PermissionError:
                print(f"{COLORS.ERROR}  [!] Permission denied. Run with sudo.{COLORS.RESET}\n")
        else:
            print(f"{COLORS.SUCCESS}  ◈ {action.capitalize()} cancelled.{COLORS.RESET}\n")

    else:
        print(f"{COLORS.ERROR}  [!] Unknown action: '{action}'{COLORS.RESET}")
        print(f"{COLORS.DIM}  Options: restart | shutdown | reboot{COLORS.RESET}\n")


# ─────────────────────────────────────────────
#  OPEN COMMAND
#  Opens external apps from within VORTEX shell.
#  'open browser'    → opens default web browser
#  'open files'      → opens file manager
#  'open terminal'   → opens a new terminal
#  'open <url>'      → opens URL in browser
# ─────────────────────────────────────────────

@with_timestamp
def cmd_open(args, config):
    """
    Command: open <target>
    Launches external applications or URLs.
    Uses subprocess so VORTEX shell doesn't freeze.
    """
    if not args:
        print(f"\n{COLORS.ERROR}  [!] Usage: open <target>{COLORS.RESET}")
        print(f"  {COLORS.DIM}Targets: browser, files, terminal, editor, <url>{COLORS.RESET}\n")
        return

    target = args[0].lower()

    # Map friendly names to actual commands
    # 'xdg-open' is the universal Linux "open with default app" command
    launchers = {
        "browser":   ["xdg-open", "https://google.com"],
        "files":     ["xdg-open", os.path.expanduser("~")],
        "terminal":  ["x-terminal-emulator"],
        "editor":    ["xdg-open", os.path.expanduser("~")],
    }

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ OPEN{COLORS.RESET}")

    # Check if target looks like a URL
    if target.startswith("http://") or target.startswith("https://") or "." in target:
        url = target if "://" in target else "https://" + target
        try:
            subprocess.Popen(["xdg-open", url],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            print(f"  {COLORS.SUCCESS}✓ Opening URL: {url}{COLORS.RESET}\n")
        except Exception as e:
            print(f"  {COLORS.ERROR}[!] Failed to open URL: {e}{COLORS.RESET}\n")
        return

    if target in launchers:
        try:
            subprocess.Popen(launchers[target],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            print(f"  {COLORS.SUCCESS}✓ Launching: {target}{COLORS.RESET}\n")
        except FileNotFoundError:
            print(f"  {COLORS.ERROR}[!] App not found for: {target}{COLORS.RESET}")
            print(f"  {COLORS.DIM}Make sure a desktop environment is running.{COLORS.RESET}\n")
    else:
        # Try to open as a raw command
        try:
            subprocess.Popen(args,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            print(f"  {COLORS.SUCCESS}✓ Launched: {' '.join(args)}{COLORS.RESET}\n")
        except FileNotFoundError:
            print(f"  {COLORS.ERROR}[!] Unknown target: '{target}'{COLORS.RESET}")
            print(f"  {COLORS.DIM}Options: browser | files | terminal | editor | <url>{COLORS.RESET}\n")