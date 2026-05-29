# commands/session_commands.py
# VORTEX OS - Session and password management commands

import os
import json
import hashlib

from themes.colors import COLORS
from commands.builtin_commands import with_timestamp

SESSION_FILE = "config/session.json"


def _load_session():
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_session(data):
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[Session] Save error: {e}")


def _hash_password(password):
    salt   = "VORTEX_OS_SALT_2025"
    salted = salt + password + salt
    return hashlib.sha256(salted.encode()).hexdigest()


@with_timestamp
def cmd_passwd(args, config):
    """
    Command: passwd
    Change the VORTEX OS login password.
    Prompts for current password then new password twice.
    """
    import getpass

    session = _load_session()
    stored  = session.get("password_hash", "")

    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ CHANGE PASSWORD{COLORS.RESET}\n")

    # If password is already set, verify current password first
    if stored:
        try:
            current = getpass.getpass(
                f"  {COLORS.PRIMARY}Current password: {COLORS.RESET}"
            )
        except (KeyboardInterrupt, EOFError):
            print(f"\n{COLORS.WARNING}  Cancelled.{COLORS.RESET}\n")
            return

        if _hash_password(current) != stored:
            print(f"\n{COLORS.ERROR}  [!] Incorrect current password."
                  f"{COLORS.RESET}\n")
            return

    # Get new password
    try:
        new_pw = getpass.getpass(
            f"  {COLORS.PRIMARY}New password: {COLORS.RESET}"
        )
        confirm = getpass.getpass(
            f"  {COLORS.PRIMARY}Confirm new password: {COLORS.RESET}"
        )
    except (KeyboardInterrupt, EOFError):
        print(f"\n{COLORS.WARNING}  Cancelled.{COLORS.RESET}\n")
        return

    if len(new_pw) < 4:
        print(f"\n{COLORS.ERROR}  [!] Password must be at least "
              f"4 characters.{COLORS.RESET}\n")
        return

    if new_pw != confirm:
        print(f"\n{COLORS.ERROR}  [!] Passwords do not match."
              f"{COLORS.RESET}\n")
        return

    session["password_hash"] = _hash_password(new_pw)
    _save_session(session)

    print(f"\n{COLORS.SUCCESS}  ✓ Password updated successfully."
          f"{COLORS.RESET}\n")


@with_timestamp
def cmd_session(args, config):
    """
    Command: session [info | logout | autologin on|off]
    Manage the current VORTEX session.
    """
    session = _load_session()

    if not args or args[0].lower() == "info":
        _session_info(session)

    elif args[0].lower() == "logout":
        _session_logout(session)

    elif args[0].lower() == "autologin":
        if len(args) < 2:
            print(f"{COLORS.ERROR}  [!] Usage: "
                  f"session autologin on|off{COLORS.RESET}\n")
            return
        _session_autologin(session, args[1].lower())

    else:
        print(f"{COLORS.ERROR}  [!] Unknown subcommand: "
              f"'{args[0]}'{COLORS.RESET}")
        print(f"  {COLORS.DIM}Options: info | logout | "
              f"autologin on|off{COLORS.RESET}\n")


def _session_info(session):
    """Shows current session details."""
    print(f"\n{COLORS.ACCENT}{COLORS.BOLD}  ◈ SESSION INFO{COLORS.RESET}\n")

    fields = [
        ("USER",       session.get("username",     "unknown")),
        ("NAME",       session.get("display_name", "unknown")),
        ("ACTIVE",     str(session.get("session_active", False))),
        ("AUTO LOGIN", str(session.get("auto_login",     False))),
        ("PW SET",     "YES" if session.get("password_hash") else "NO"),
        ("MAX TRIES",  str(session.get("max_attempts", 5))),
    ]

    for label, value in fields:
        print(f"  {COLORS.PRIMARY}{label:<14}{COLORS.TEXT}{value}")
    print()


def _session_logout(session):
    """Marks session as inactive."""
    session["session_active"] = False
    _save_session(session)
    print(f"\n{COLORS.SUCCESS}  ✓ Session logged out.{COLORS.RESET}")
    print(f"  {COLORS.DIM}Restart VORTEX to return to "
          f"login screen.{COLORS.RESET}\n")


def _session_autologin(session, value):
    """Enables or disables auto-login."""
    if value in ("on", "true", "yes", "1"):
        session["auto_login"] = True
        _save_session(session)
        print(f"\n{COLORS.SUCCESS}  ✓ Auto-login enabled. "
              f"Login screen will be skipped.{COLORS.RESET}\n")
    elif value in ("off", "false", "no", "0"):
        session["auto_login"] = False
        _save_session(session)
        print(f"\n{COLORS.SUCCESS}  ✓ Auto-login disabled.{COLORS.RESET}\n")
    else:
        print(f"{COLORS.ERROR}  [!] Use 'on' or 'off'.{COLORS.RESET}\n")