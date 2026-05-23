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

class ChainedCommand:
    """
    Represents multiple commands joined with &&.
    
    Example:
        Input:  "clock && system && whoami"
        Result: ChainedCommand(commands=[
                    ParsedCommand(command='clock', ...),
                    ParsedCommand(command='system', ...),
                    ParsedCommand(command='whoami', ...),
                ])
    
    Why a separate class instead of a list?
    Because the router checks the type of what it receives.
    isinstance(result, ChainedCommand) is explicit and readable.
    """

    def __init__(self, commands):
        # commands is a list of ParsedCommand objects
        self.commands = commands

    def __repr__(self):
        return f"ChainedCommand(count={len(self.commands)}, commands={self.commands})"

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
    Main parse method.
    
    Now handles command chaining with &&.
    
    Returns:
        None           → empty input
        ParsedCommand  → single command
        ChainedCommand → multiple commands joined with &&
    """
     if not raw_input or not raw_input.strip():
        return None

    # Step 1: Check for && BEFORE alias expansion
    # Why before? Because an alias could contain && itself in theory,
    # and we want user-typed && to always mean chaining.
     if "&&" in raw_input:
        return self._parse_chained(raw_input)

    # Single command path (existing logic)
     return self._parse_single(raw_input.strip())

    def _parse_single(self, raw_input):
     """
    Parses a single command string.
    Extracted from old parse() so chained parsing can reuse it.
    """
    # Expand aliases
     expanded = self._expand_alias(raw_input.strip())

    # Tokenize (respects quoted strings)
     try:
         tokens = shlex.split(expanded)
     except ValueError:
        tokens = expanded.split()

     if not tokens:
        return None

     command = tokens[0].lower()
     args    = tokens[1:]

     return ParsedCommand(
        command=command,
        args=args,
        full_command=expanded,
        raw_input=raw_input
    )

    def _parse_chained(self, raw_input):
     """
    Splits input on && and parses each fragment individually.
    
    Fragments that are empty (e.g. 'clock &&') are skipped.
    Each fragment gets alias expansion independently.
    
    Example:
        "ls && me && v"
        Split  → ["ls ", " me ", " v"]
        Parse  → [vault list, whoami, version]
    """
    # Split on && — each fragment is one command
     fragments = raw_input.split("&&")

     parsed_list = []
     for fragment in fragments:
        fragment = fragment.strip()

        # Skip empty fragments (e.g. trailing &&)
        if not fragment:
            continue

        # Parse each fragment as an individual command
        parsed = self._parse_single(fragment)
        if parsed is not None:
            parsed_list.append(parsed)

    # If somehow nothing parsed, return None
     if not parsed_list:
        return None

    # Single command after splitting? Return as plain ParsedCommand
     if len(parsed_list) == 1:
        return parsed_list[0]

     return ChainedCommand(commands=parsed_list)