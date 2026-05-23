# terminal/shell.py
# VORTEX OS - Core Shell Loop
# This is the heart of the terminal. It reads input, calls commands.

import json
import os

from themes.colors import COLORS
from commands.builtin_commands import (
    cmd_help,
    cmd_clock,
    cmd_clear,
    cmd_system,
    cmd_exit,
    cmd_version,    
    cmd_whoami,
)


class VortexShell:
    """
    The main VORTEX terminal shell.
    
    Responsibilities:
    - Load configuration
    - Display the startup banner
    - Run the input loop
    - Route commands to handler functions
    - Handle unknown commands and errors
    """

    def __init__(self, config_path="config/settings.json"):
        """
        Constructor — runs when we create a VortexShell object.
        Loads the JSON config file immediately.
        """
        self.config = self._load_config(config_path)
        
        # The prompt string shown before every input
        self.prompt = self.config.get("prompt", "[VORTEX@CORE] > ")
        
        # Command registry — maps typed words to functions
        # This is the key design pattern: dict lookup instead of if/elif chains
        self.commands = {
            "help":   cmd_help,
            "clock":  cmd_clock,
            "clear":  cmd_clear,
            "system": cmd_system,
            "exit":   cmd_exit,
            "quit":   cmd_exit, 
            "version": cmd_version, 
            "whoami": cmd_whoami, # alias for exit
        }

    def _load_config(self, path):
        """
        Private method (notice the underscore prefix).
        Reads and parses the JSON config file.
        Returns the config dict, or defaults if file not found.
        """
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{COLORS.WARNING}[WARN] Config file not found. Using defaults.{COLORS.RESET}")
            return {
                "os_name": "VORTEX OS",
                "version": "0.1.0",
                "codename": "GENESIS",
                "prompt": "[VORTEX@CORE] > "
            }

    def _print_banner(self):
    
     banner_cfg = self.config.get("banner", {})
     show_ascii  = banner_cfg.get("show_ascii", True)
     tagline     = banner_cfg.get("tagline", "")
     show_hints  = banner_cfg.get("show_hints", True)

     if show_ascii:
        ascii_art = f"""
{COLORS.PRIMARY}{COLORS.BOLD}
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{COLORS.RESET}"""
        print(ascii_art)

     print(f"  {COLORS.ACCENT}◈ {self.config['os_name']} v{self.config['version']} [{self.config['codename']}]{COLORS.RESET}")

     if tagline:
        print(f"  {COLORS.DIM}{tagline}{COLORS.RESET}")

     if show_hints:
        print(f"\n  {COLORS.DIM}Type 'help' to see available commands.{COLORS.RESET}")
        print(f"  {COLORS.DIM}Type 'exit' to quit.{COLORS.RESET}")

    print()

    def _parse_input(self, raw_input):
        """
        Splits raw typed input into command + arguments.
        
        Example:
            'open browser'  → ('open', ['browser'])
            'theme neon'    → ('theme', ['neon'])
            'help'          → ('help', [])
            '  '            → (None, [])
        """
        # Strip leading/trailing whitespace
        cleaned = raw_input.strip()
        
        # Empty input → return nothing
        if not cleaned:
            return None, []
        
        # Split on spaces
        parts = cleaned.split()
        
        # First word is the command, rest are arguments
        command = parts[0].lower()
        args = parts[1:]
        
        return command, args

    def run(self):
        """
        The main shell loop.
        This runs forever until the user types 'exit'.
        """
        # Show the banner first
        self._print_banner()

        # Infinite loop — the shell keeps running
        while True:
            try:
                # Print prompt and wait for input
                # end='' and flush=True ensure prompt shows on same line
                 # Get current directory, replace /home/username with ~ for cleanliness
                 cwd = os.getcwd()
                 home = os.path.expanduser("~")

# If we're inside the home directory, show ~ instead of full path
                 if cwd.startswith(home):
                   cwd = "~" + cwd[len(home):]

# Build dynamic prompt with directory injected
                 dynamic_prompt = f"[VORTEX@CORE {cwd}] > "

                 raw = input(f"{COLORS.PRIMARY}{dynamic_prompt}{COLORS.RESET}")

            except KeyboardInterrupt:
                # User pressed Ctrl+C — don't crash, just show a message
                print(f"\n{COLORS.WARNING}  [!] Use 'exit' to quit VORTEX.{COLORS.RESET}")
                continue

            except EOFError:
                # User pressed Ctrl+D — treat as exit
                print()
                break

            # Parse what was typed
            command, args = self._parse_input(raw)

            # Empty input — just show the prompt again
            if command is None:
                continue

            # Look up the command in our registry
            if command in self.commands:
                try:
                    # Call the command function, pass args and config
                    result = self.commands[command](args, self.config)
                    
                    # If the function returned "EXIT", break the loop
                    if result == "EXIT":
                        break

                except Exception as e:
                    # Something crashed inside the command — catch it gracefully
                    print(f"{COLORS.ERROR}  [ERROR] Command '{command}' failed: {e}{COLORS.RESET}")

            else:
                # Command not found
                print(f"\n{COLORS.ERROR}  [!] Unknown command: '{command}'{COLORS.RESET}")
                print(f"{COLORS.DIM}  Type 'help' to see available commands.{COLORS.RESET}\n")
