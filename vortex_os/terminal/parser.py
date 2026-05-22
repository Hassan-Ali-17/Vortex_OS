# terminal/parser.py
# VORTEX OS - Command Parser
# Converts raw string input into structured ParsedCommand objects.

import json
import os
import shlex


class ParsedCommand:
    """
    A structured representation of a parsed command.
    
    Instead of passing (command_string, args_list) around everywhere,
    we use this object. It's cleaner and extensible.
    
    Example:
        Input:  'open browser'
        Result: ParsedCommand(command='open', args=['browser'],
                              full='open browser', raw='open browser')
    """

    def __init__(self, command, args, full_command, raw_input):
        self.command      = command       # First word (the verb)
        self.args         = args          # Remaining words (the arguments)
        self.full_command = full_command  # Full normalized string after alias expansion
        self.raw_input    = raw_input     # Exactly what the user typed

    def __repr__(self):
        return (f"ParsedCommand(command={self.command!r}, "
                f"args={self.args}, full={self.full_command!r})")


class CommandParser:
    """
    Parses raw terminal input into ParsedCommand objects.
    Also handles alias resolution.
    
    This class does NOT know about command handlers — that's the router's job.
    Single responsibility: understand input, nothing more.
    """

    def __init__(self, aliases_path="config/aliases.json"):
        self.aliases = self._load_aliases(aliases_path)

    def _load_aliases(self, path):
        """
        Loads aliases from JSON.
        Returns empty dict if file is missing — aliases are optional.
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get("aliases", {})
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            print(f"[WARN] aliases.json is malformed: {e}")
            return {}

    def _expand_alias(self, raw_input):
        """
        Checks if the input (or first word) is an alias.
        If so, replaces it with the full command.
        
        Examples:
            'q'         → 'exit'
            'ls'        → 'vault list'
            'ls /home'  → 'vault list /home'  (args preserved)
        """
        stripped = raw_input.strip()

        # Check if the full input matches an alias
        if stripped in self.aliases:
            return self.aliases[stripped]

        # Check if just the first word is an alias
        parts = stripped.split()
        if parts and parts[0] in self.aliases:
            # Replace first word with alias expansion, keep remaining args
            expanded = self.aliases[parts[0]]
            extra_args = parts[1:]
            if extra_args:
                return expanded + ' ' + ' '.join(extra_args)
            return expanded

        # No alias found — return original
        return raw_input

    def parse(self, raw_input):
        """
        Main parse method. Takes raw string, returns ParsedCommand or None.
        
        Returns None for empty input so the shell can skip gracefully.
        """
        if not raw_input or not raw_input.strip():
            return None

        # Step 1: Expand aliases
        expanded = self._expand_alias(raw_input.strip())

        # Step 2: Split into tokens
        # We use shlex.split() instead of str.split() because it respects
        # quoted strings. Example:
        #   shlex.split('open "my file"') → ['open', 'my file']
        #   str.split('open "my file"')   → ['open', '"my', 'file"']
        try:
            tokens = shlex.split(expanded)
        except ValueError:
            # shlex fails on unmatched quotes — fall back to simple split
            tokens = expanded.split()

        if not tokens:
            return None

        # Step 3: First token is the command, rest are args
        command = tokens[0].lower()
        args    = tokens[1:]

        return ParsedCommand(
            command=command,
            args=args,
            full_command=expanded,
            raw_input=raw_input
        )