# terminal/router.py
# VORTEX OS - Command Router
# Maps parsed commands to handler functions and executes them.

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
        Executes a ParsedCommand.
        
        Returns:
            "EXIT"  → shell should stop
            None    → continue normally
        
        Raises nothing — all errors are caught and displayed cleanly.
        """
        if parsed_command is None:
            return None

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
            # Uncomment the next line during debugging to see full stack trace:
            # import traceback; traceback.print_exc()
            return None