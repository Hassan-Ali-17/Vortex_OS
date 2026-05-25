<br>

<div align="center">

```
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
```

</div>

<div align="center">
**VORTEX OS** · `v0.1.0` · Codename **GENESIS**

*A custom Linux-based pseudo operating system built on Ubuntu.*
*Custom shell · Desktop environment · Terminal ecosystem.*

![Python](https://img.shields.io/badge/Python-3.10%2B-cyan?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Ubuntu%20Linux-orange?style=flat-square)
![Phase](https://img.shields.io/badge/Current%20Phase-3%20of%2015-magenta?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active%20Development-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

</div>

---

## What is VORTEX OS?

VORTEX OS is a custom Linux-based operating environment built on top of Ubuntu. It is **not** a new kernel — it is a fully custom shell, desktop environment, and terminal ecosystem that progressively evolves into a bootable Linux distribution across 15 development phases.

It is built entirely in **Python**, styled with **cyberpunk aesthetics**, and designed to be lightweight enough to run on a machine with **4 GB of RAM**.

---

## Project Philosophy

| Principle | Implementation |
|---|---|
| Modular architecture | Every feature lives in its own folder and file |
| Lightweight | No heavy frameworks; pure Python stdlib where possible |
| Beginner-friendly | Every file is commented line-by-line |
| Extensible | Adding a command = adding one function + one line |
| Cyberpunk aesthetic | Custom colors, ASCII art, themed prompt, glyphs |
| Config-driven | JSON files control behavior — no hardcoding |

---

## Current Project Structure

```
vortex_os/
│
├── main.py                        ← Single entry point. Run this.
│
├── core/
│   ├── __init__.py
│   └── vortex_core.py             ← Boot sequence, startup sound
│
├── terminal/
│   ├── __init__.py
│   ├── shell.py                   ← Main REPL loop, prompt, input
│   ├── parser.py                  ← Input parsing, alias expansion, chaining
│   ├── router.py                  ← Command registry and dispatch
│   └── history.py                 ← readline integration, JSON persistence
│
├── commands/
│   ├── __init__.py
│   ├── builtin_commands.py        ← help, clock, clear, system, exit, version, whoami
│   ├── system_commands.py         ← vault, scan, apps, ignite, open
│   └── theme_commands.py          ← theme, history
│
├── themes/
│   ├── __init__.py
│   ├── colors.py                  ← Legacy compatibility shim
│   └── theme_engine.py            ← 6 themes, live switching, color proxy
│
├── config/
│   ├── settings.json              ← OS name, version, banner, active theme
│   ├── aliases.json               ← User-defined command aliases
│   └── history.json               ← Persisted command history (auto-generated)
│
├── assets/                        ← Audio, images (future phases)
├── gui/                           ← PyQt6 desktop (Phase 5+)
├── widgets/                       ← Clock, calendar widgets (Phase 4+)
└── apps/                          ← App system (Phase 9+)
```

---

## Quickstart

### Requirements

- Ubuntu 20.04 or later
- Python 3.10 or later
- pip3

### Install dependencies

```bash
pip3 install colorama
```

### Clone or set up the project

```bash
mkdir ~/vortex_os
cd ~/vortex_os
# (copy all project files here)
```

### Run VORTEX OS

```bash
cd ~/vortex_os
python3 main.py
```

You will see the VORTEX ASCII banner and the custom prompt:

```
[VORTEX@CORE ~/vortex_os] >
```

---

## All Available Commands

### Built-in Commands

| Command | Description |
|---|---|
| `help` | Show all available commands |
| `clock` | Show current date and time |
| `clock live` | Live ticking clock mode (Ctrl+C to exit) |
| `clear` | Clear the terminal screen |
| `system` | Show CPU, RAM, OS, architecture info |
| `version` | Show VORTEX OS version from config |
| `whoami` | Show current Linux user identity and groups |
| `exit` / `quit` | Exit the VORTEX terminal |

### System Commands

| Command | Description |
|---|---|
| `vault` | List current directory |
| `vault list <path>` | List contents of any path |
| `vault go <path>` | Navigate to a directory |
| `vault info <path>` | Show file/folder metadata |
| `vault find <name>` | Recursively search for files by name |
| `scan` | System health: RAM, CPU load, disk usage |
| `scan ports` | Show listening TCP ports |
| `scan network` | Show network interfaces |
| `scan disk` | Show disk usage with df |
| `apps` | List VORTEX OS application registry |
| `ignite` | Show power menu |
| `ignite restart` | Restart the VORTEX terminal process |
| `ignite shutdown` | Shutdown system (confirmation required) |
| `ignite reboot` | Reboot system (confirmation required) |
| `open browser` | Open default web browser |
| `open files` | Open file manager |
| `open <url>` | Open a URL in the browser |

### Theme Commands

| Command | Description |
|---|---|
| `theme` | List all available themes |
| `theme <name>` | Switch to a named theme (persists to config) |
| `theme preview` | Color swatch of the active theme |
| `theme animate` | Cycle through all themes with live preview |

### History Commands

| Command | Description |
|---|---|
| `history` | Show last 15 commands |
| `history <n>` | Show last n commands |
| `history clear` | Clear all history |
| `history search <word>` | Filter history by keyword with highlighting |

---

## Aliases

Aliases are defined in `config/aliases.json` and expand at parse time.

| Alias | Expands To |
|---|---|
| `q` | `exit` |
| `h` | `help` |
| `v` | `version` |
| `cls` | `clear` |
| `top` | `system` |
| `time` | `clock` |
| `ls` | `vault list` |
| `me` | `whoami` |
| `boot` | `ignite` |
| `heck` | `scan` |
| `ping` | `scan network` |
| `th` | `theme` |
| `hist` | `history` |

Add your own aliases by editing `config/aliases.json` — no Python changes needed.

---

## Command Chaining

Commands can be chained with `&&`. They execute in order, left to right.

```
clock && system
whoami && version && apps
ls && me && v
vault find py && scan
```

If any command returns `EXIT`, the chain stops immediately.

---

## Available Themes

| Theme | Description |
|---|---|
| `cyberpunk` | Electric cyan on black — the default |
| `matrix` | All green — follow the white rabbit |
| `blood` | Red and white — danger mode |
| `ghost` | White and grey — minimal stealth |
| `solar` | Amber and gold — warm retro terminal |
| `arctic` | Ice blue and white — cool and clean |

Switch themes live with `theme <name>`. The choice persists across restarts.

---

## Configuration

### `config/settings.json`

Controls OS identity and startup behavior.

```json
{
    "os_name": "VORTEX OS",
    "version": "0.1.0",
    "codename": "GENESIS",
    "prompt": "[VORTEX@CORE] > ",
    "author": "VORTEX TEAM",
    "terminal_title": "VORTEX TERMINAL",
    "default_theme": "cyberpunk",
    "banner": {
        "show_ascii": true,
        "tagline": "INITIALIZE. DOMINATE. EVOLVE.",
        "show_hints": true
    }
}
```

### `config/aliases.json`

User-defined command shortcuts. Edit freely — no restart needed for next session.

### `config/history.json`

Auto-generated. Stores up to 500 commands. Survives restarts.

---

## Architecture Deep Dive

### How a command executes

```
python3 main.py
  └── VortexCore.boot()
        └── VortexShell.run()
              └── input() → raw string
                    └── HistoryManager.add()
                    └── CommandParser.parse()
                          ├── alias expansion
                          ├── && chain detection
                          └── shlex tokenization
                                └── ParsedCommand / ChainedCommand
                                      └── CommandRouter.execute()
                                            └── handler_function(args, config)
```

### Key Design Patterns Used

**Registry / Dispatcher** — `CommandRouter` maintains a dict of `name → function`. Adding a command is one `register()` call.

**Decorator** — `@with_timestamp` wraps every command function to print execution time without modifying the function itself.

**Proxy** — `_ColorProxy` in `theme_engine.py` intercepts attribute access so `COLORS.PRIMARY` always returns the *current* theme's color, enabling live theme switching with zero code changes elsewhere.

**Dependency Injection** — The `config` dict carries `_router` and `_history` references so commands can access these services without importing them directly.

**Single Responsibility** — Parser parses. Router routes. Commands do their job. Shell loops. Core boots. Nothing does two jobs.

---

## Development Phases

| Phase | Title | Status |
|---|---|---|
| **1** | Project setup + custom terminal shell | ✅ Complete |
| **2** | Command parser + internal commands + aliases | ✅ Complete |
| **3** | Theme engine + command history + readline | ✅ Complete |
| **4** | Clock + calendar PyQt6 widgets | 🔄 Next |
| **5** | PyQt6 GUI desktop window | ⏳ Planned |
| **6** | Dock + launcher + panels | ⏳ Planned |
| **7** | Filesystem abstraction + VORTEX directories | ⏳ Planned |
| **8** | Multi-tab terminal | ⏳ Planned |
| **9** | App system | ⏳ Planned |
| **10** | Boot animation + startup screen | ⏳ Planned |
| **11** | Login screen | ⏳ Planned |
| **12** | AI assistant integration | ⏳ Planned |
| **13** | Voice assistant | ⏳ Planned |
| **14** | ISO customization | ⏳ Planned |
| **15** | Bootable VORTEX OS image | ⏳ Planned |

---

## Dependencies

| Package | Version | Purpose | Install |
|---|---|---|---|
| `colorama` | Latest | Cross-platform terminal colors | `pip3 install colorama` |
| `PyQt6` | Latest | GUI desktop environment (Phase 5+) | `pip3 install PyQt6` |

Everything else uses Python's standard library: `os`, `sys`, `json`, `subprocess`, `readline`, `platform`, `datetime`, `shutil`, `shlex`, `grp`.

---

## Keyboard Shortcuts (Terminal)

| Key | Action |
|---|---|
| `↑` | Previous command |
| `↓` | Next command |
| `←` `→` | Move cursor |
| `Home` / `Ctrl+A` | Jump to start of line |
| `End` / `Ctrl+E` | Jump to end of line |
| `Ctrl+U` | Clear current line |
| `Ctrl+C` | Interrupt current command / return to prompt |
| `Ctrl+D` | Exit terminal (EOF) |

---

## Known Limitations (Phase 3)

- `open` commands require a running desktop environment (X11/Wayland)
- `ignite shutdown` and `ignite reboot` require `sudo` privileges
- Startup sound requires PulseAudio (`paplay`) to be available
- No autocomplete yet (coming in Phase 4/5)
- No GUI desktop yet (coming in Phase 5)

---

## Contributing / Extending

### Adding a new command

1. Write a function in `commands/your_file.py`:
```python
@with_timestamp
def cmd_yourcommand(args, config):
    print("Hello from my command!")
```

2. Import it in `terminal/shell.py`
3. Register it in `_register_commands()`:
```python
"yourcommand": (cmd_yourcommand, "Does something cool"),
```

That's it. The router, help menu, and history all pick it up automatically.

### Adding a new theme

Open `themes/theme_engine.py` and add an entry to the `THEMES` dict:

```python
"mytheme": {
    "name":        "MYTHEME",
    "description": "My custom color scheme.",
    "PRIMARY":     Fore.LIGHTBLUE_EX,
    "SUCCESS":     Fore.GREEN,
    "WARNING":     Fore.YELLOW,
    "ERROR":       Fore.RED,
    "ACCENT":      Fore.BLUE,
    "TEXT":        Fore.WHITE,
    "DIM":         Fore.LIGHTBLACK_EX,
    "BOLD":        Style.BRIGHT,
    "RESET":       Style.RESET_ALL,
},
```

Then `theme mytheme` works immediately.

---

## License

MIT License — free to use, modify, and distribute.

---

<div align="center">

*Built phase by phase. No shortcuts. No zip files.*
*INITIALIZE. DOMINATE. EVOLVE.*

**VORTEX OS** · Phase 3 · GENESIS

</div>

