# terminal/shell.py
# VORTEX OS - Core Shell Loop (Phase 2 Refactor)
# Now delegates parsing and routing to dedicated classes.

import json
import os
from terminal.history import HistoryManager
from commands.theme_commands import cmd_theme, cmd_history
# Add to imports in terminal/shell.py
from commands.widget_commands import cmd_clock_gui, cmd_calendar, cmd_widgets, cmd_desktop , cmd_monitor , cmd_newtab ,  cmd_reboot_anim   
from commands.session_commands import cmd_passwd, cmd_session
from commands.fs_commands import cmd_vx, cmd_landmark, cmd_vault_vx
from themes.colors import COLORS
from terminal.parser import CommandParser
from terminal.router import CommandRouter
from commands.app_commands import cmd_app
from commands.ai_commands import cmd_aria


# Phase 1 commands
from commands.builtin_commands import (
    cmd_help,
    cmd_clock,
    cmd_clear,
    cmd_system,
    cmd_exit,
    cmd_version,
    cmd_whoami,
)

# Phase 2 commands
from commands.system_commands import (
    cmd_vault,
    cmd_scan,
    cmd_apps,
    cmd_ignite,
    cmd_open,
)


class VortexShell:
    """
    VORTEX terminal shell — Phase 2.
    
    Changes from Phase 1:
    - Uses CommandParser for input parsing + alias resolution
    - Uses CommandRouter for command dispatch
    - Shell itself is now thin — just the loop and display
    """

    def __init__(self, config_path="config/settings.json"):
     self.config = self._load_config(config_path)
     self.parser = CommandParser(aliases_path="config/aliases.json")
     self.router = CommandRouter()

    # Create history manager and inject into config
     self.history = HistoryManager()
     self.config["_history"] = self.history      # ← ADD
 
     self._register_commands()
    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{COLORS.WARNING}[WARN] Config not found. Using defaults.{COLORS.RESET}")
            return {
                "os_name": "VORTEX OS",
                "version": "0.1.0",
                "codename": "GENESIS",
                "prompt": "[VORTEX@CORE] > ",
                "banner": {}
            }

    def _register_commands(self):
        """
        Registers all commands with the router.
        This is the ONE place where commands are declared.
        Adding a new command = adding one line here.
        """
        self.router.register_many({
            # name:        (handler,      description)
            "help":        (cmd_help,     "Show command reference"),
            "clock":       (cmd_clock,    "Show time | clock live for live mode"),
            "clear":       (cmd_clear,    "Clear the terminal screen"),
            "system":      (cmd_system,   "Show system hardware info"),
            "exit":        (cmd_exit,     "Exit VORTEX terminal"),
            "quit":        (cmd_exit,     "Exit VORTEX terminal"),
            "version":     (cmd_version,  "Show VORTEX OS version"),
            "whoami":      (cmd_whoami,   "Show current user identity"),
            "vault":       (cmd_vault,    "Filesystem explorer"),
            "scan":        (cmd_scan,     "System & network scanner"),
            "apps":        (cmd_apps,     "List VORTEX applications"),
            "ignite":      (cmd_ignite,   "Power control (restart/shutdown/reboot)"),
            "open":        (cmd_open,     "Launch apps or URLs"),
            "theme":       (cmd_theme,   "Switch color themes"),
            "history":     (cmd_history, "View or clear command history"),
            "clock gui":   (cmd_clock_gui,  "Launch floating clock widget"),
            "calendar":    (cmd_calendar,   "Launch floating calendar widget"),
            "widgets":     (cmd_widgets,    "List available widgets"),
            "desktop":     (cmd_desktop, "Show the VORTEX desktop window"),
            "monitor":     (cmd_monitor, "Launch system monitor widget"),
            "vx":          (cmd_vx,       "VORTEX virtual navigator"),
            "landmark":    (cmd_landmark, "Manage filesystem landmarks"),
            "newtab":      (cmd_newtab, "Open new tab in desktop terminal"),
            "app":         (cmd_app, "App system — list, launch, install"),
            "reboot":      (cmd_reboot_anim, "Replay boot animation"),
            "passwd":      (cmd_passwd,  "Change VORTEX login password"),
            "session":     (cmd_session, "Session info and management"),
            "aria":        (cmd_aria, "Open ARIA AI assistant"),

        })

        self.config["_router"] = self.router

    def _print_banner(self):
        banner_cfg  = self.config.get("banner", {})
        show_ascii  = banner_cfg.get("show_ascii", True)
        tagline     = banner_cfg.get("tagline", "")
        show_hints  = banner_cfg.get("show_hints", True)

        if show_ascii:
            print(f"""
{COLORS.PRIMARY}{COLORS.BOLD}
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{COLORS.RESET}""")

        print(f"  {COLORS.ACCENT}◈ {self.config['os_name']} v{self.config['version']} [{self.config['codename']}]{COLORS.RESET}")

        if tagline:
            print(f"  {COLORS.DIM}{tagline}{COLORS.RESET}")

        if show_hints:
            print(f"\n  {COLORS.DIM}Type 'help' to see available commands.{COLORS.RESET}")
            print(f"  {COLORS.DIM}Type 'exit' to quit.{COLORS.RESET}")

        print()

    def run(self):
     """Main shell loop."""
     self._print_banner()

     while True:
        try:
            # ── Build VX-aware prompt ──────────────
            real_cwd = os.getcwd()

            # Try to get vx:// display path
            try:
                from core.filesystem import get_vfs
                vfs      = get_vfs()
                cwd_disp = vfs.display_path(real_cwd)
            except Exception:
                # Fallback: compress home with ~
                home     = os.path.expanduser("~")
                cwd_disp = ("~" + real_cwd[len(home):]
                            if real_cwd.startswith(home)
                            else real_cwd)

            prompt = f"[VORTEX@CORE {cwd_disp}] > "

            raw = input(f"{COLORS.PRIMARY}{prompt}{COLORS.RESET}")

        except KeyboardInterrupt:
            print(f"\n{COLORS.WARNING}  [!] Use 'exit' to quit.{COLORS.RESET}")
            continue
        except EOFError:
            break

        if raw.strip():
            self.history.add(raw.strip())

        parsed = self.parser.parse(raw)
        if parsed is None:
            continue

        result = self.router.execute(parsed, self.config)
        if result == "EXIT":
            break