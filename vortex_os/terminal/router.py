# terminal/router.py
# VORTEX OS - Command Router
# Maps parsed commands to handler functions and executes them.
from terminal.parser import ChainedCommand
from themes.colors import COLORS


class CommandRouter:
    """
    Maintains a registry of command handlers and routes
    ParsedCommand objects to the correct one.
    
    Design pattern: Registry / Dispatcher
    
    This replaces the dict in shell.py with a proper class
    that can do validation, logging, and error handling.
    """

    def __init__(self):
        # Internal registry: { "command_name": handler_function }
        self._registry = {}
        
        # Help metadata: { "command_name": "description" }
        self._help_data = {}

    def register(self, name, handler, description=""):
        """
        Registers a command handler.
        
        Args:
            name:        The command word the user types (e.g. 'clock')
            handler:     The function to call (e.g. cmd_clock)
            description: One-line description for the help menu
        
        Example:
            router.register('clock', cmd_clock, 'Display current time')
        """
        self._registry[name.lower()] = handler
        self._help_data[name.lower()] = description

    def register_many(self, commands_dict):
        """
        Convenience method to register multiple commands at once.
        
        Args:
            commands_dict: {
                'name': (handler_function, 'description'),
                ...
            }
        """
        for name, (handler, description) in commands_dict.items():
            self.register(name, handler, description)

    def get_all_commands(self):
        """
        Returns list of (name, description) tuples for all registered commands.
        Used by the help system.
        """
        return sorted(
            [(name, desc) for name, desc in self._help_data.items()],
            key=lambda x: x[0]  # Sort alphabetically
        )

    def knows(self, command_name):
        """Returns True if this command is registered."""
        return command_name.lower() in self._registry

    def execute(self, parsed_command, config):
     """
    Executes a ParsedCommand or ChainedCommand.
    
    For chained commands:
    - Runs each command in sequence
    - If any command returns "EXIT", stops the chain and exits
    - Prints a separator between chained outputs for readability
    
    Returns:
        "EXIT" → shell should stop
        None   → continue normally
     """
     if parsed_command is None:
        return None

    # Handle chained commands
     if isinstance(parsed_command, ChainedCommand):
        return self._execute_chain(parsed_command, config)

    # Single command (original logic)
     return self._execute_single(parsed_command, config)

    def _execute_single(self, parsed_command, config):
     """Executes one ParsedCommand. (Extracted from old execute())"""
     name = parsed_command.command

     if name not in self._registry:
        print(f"\n{COLORS.ERROR}  [!] Unknown command: '{name}'{COLORS.RESET}")
        print(f"{COLORS.DIM}  Type 'help' to see available commands.{COLORS.RESET}\n")
        return None

     handler = self._registry[name]

     try:
        result = handler(parsed_command.args, config)
        return result
     except Exception as e:
        print(f"{COLORS.ERROR}  [ERROR] '{name}' crashed: {e}{COLORS.RESET}")
        return None

    def _execute_chain(self, chained, config):
     """
    Executes a ChainedCommand — runs each command in order.
    
    Behaviour:
    - Each command runs regardless of whether the previous succeeded
      (this is like '||' in Bash — Phase 3 can add strict && behaviour)
    - EXIT from any command stops the entire chain
    - A visual separator is printed between commands
    """
     total = len(chained.commands)

     print(f"{COLORS.DIM}  ── chaining {total} commands ──{COLORS.RESET}")

     for i, cmd in enumerate(chained.commands):
        # Visual separator between commands (not before the first)
        if i > 0:
            print(f"{COLORS.DIM}  ──────────────────────────────{COLORS.RESET}")

        result = self._execute_single(cmd, config)

        # If any command signals exit, stop the chain immediately
        if result == "EXIT":
            return "EXIT"

     print(f"{COLORS.DIM}  ── chain complete ──{COLORS.RESET}\n")
     return None