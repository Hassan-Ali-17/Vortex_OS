<div align="center">

```
██╗   ██╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
██║   ██║██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
██║   ██║██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝ 
╚██╗ ██╔╝██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗ 
 ╚████╔╝ ╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
```


# VORTEX OS

**A custom Linux-based operating environment built on Ubuntu.**  
*Custom shell · Desktop environment · Terminal ecosystem · App system*

[![Python](https://img.shields.io/badge/Python-3.10%2B-cyan?style=flat-square)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-magenta?style=flat-square)](https://pypi.org/project/PyQt6/)
[![Platform](https://img.shields.io/badge/Platform-Ubuntu%20Linux-orange?style=flat-square)](https://ubuntu.com)
[![Phase](https://img.shields.io/badge/Current%20Phase-10%20of%2015-green?style=flat-square)](#development-phases)
[![Author](https://img.shields.io/badge/Author-Hassan%20Ali%20Shah-cyan?style=flat-square)](https://github.com/Hassan-Ali-17)
[![GitHub](https://img.shields.io/badge/GitHub-Hassan__Ali--17-blue?style=flat-square&logo=github)](https://github.com/Hassan-Ali-17)

---

*INITIALIZE. DOMINATE. EVOLVE.*

</div>

---

## About VORTEX OS

VORTEX OS is a custom Linux-based operating environment built entirely in Python on top of Ubuntu. It is **not** a new kernel — it is a fully custom shell, desktop environment, terminal ecosystem, and application system that progressively evolves into a bootable Linux distribution across 15 development phases.

Built from scratch with cyberpunk aesthetics, modular architecture, and a philosophy of understanding every line of code written.

---

## Author

<div align="center">

### **Hassan Ali Shah**
#### GitHub: [@Hassan_Ali-17](https://github.com/Hassan-Ali-17)

*Architect, engineer, and sole developer of VORTEX OS.*  
*Built phase by phase. No shortcuts. No zip files.*

</div>

---

## Project Philosophy

| Principle | How it is applied |
|---|---|
| **Modular architecture** | Every feature lives in its own folder and file |
| **Lightweight** | No heavy frameworks — pure Python stdlib where possible |
| **Beginner-friendly** | Every file is commented line by line |
| **Extensible** | Adding a command = one function + one registration line |
| **Cyberpunk aesthetic** | Custom colors, ASCII art, themed prompt, Unicode glyphs |
| **Config-driven** | JSON files control all behavior — nothing hardcoded |
| **No shortcuts** | Every phase built and understood before moving to the next |

---

## Quickstart

### Requirements

- Ubuntu 20.04 or later
- Python 3.10 or later
- pip3

### Install dependencies

```bash
pip3 install colorama PyQt6
```

### Run VORTEX OS

```bash
cd ~/vortex_os
python3 main.py
```

The boot animation plays, then the desktop and console terminal launch together.

---

## Project Structure

```
vortex_os/
│
├── main.py                        ← Single entry point
│
├── core/
│   ├── __init__.py
│   ├── app_manager.py             ← QApplication owner, signal hub
│   ├── filesystem.py              ← Virtual filesystem (vx:// paths)
│   └── vortex_core.py             ← Boot sequence coordinator
│
├── terminal/
│   ├── __init__.py
│   ├── shell.py                   ← Main REPL loop and prompt
│   ├── parser.py                  ← Input parsing, alias expansion, chaining
│   ├── router.py                  ← Command registry and dispatch
│   └── history.py                 ← readline integration, JSON persistence
│
├── commands/
│   ├── __init__.py
│   ├── builtin_commands.py        ← help, clock, clear, system, exit, version, whoami
│   ├── system_commands.py         ← vault, scan, apps, ignite, open
│   ├── theme_commands.py          ← theme, history
│   ├── widget_commands.py         ← clock gui, calendar, monitor, desktop, reboot
│   ├── fs_commands.py             ← vx, landmark, vault (vx-aware)
│   └── app_commands.py            ← app list, launch, info, install, uninstall
│
├── gui/
│   ├── __init__.py
│   ├── boot_screen.py             ← Cinematic boot animation (Phase 10)
│   ├── desktop.py                 ← Main desktop window
│   ├── topbar.py                  ← Top bar: clock, stats
│   ├── sidebar.py                 ← Left dock with app buttons
│   ├── taskbar.py                 ← Bottom taskbar
│   ├── terminal_widget.py         ← Embedded single terminal session
│   ├── tab_bar.py                 ← Custom tab bar widget
│   ├── tab_terminal.py            ← Multi-tab terminal container
│   ├── app_launcher.py            ← Slide-out app launcher panel
│   ├── context_menu.py            ← Right-click desktop menu
│   └── styles.py                  ← All Qt stylesheets in one place
│
├── widgets/
│   ├── __init__.py
│   ├── base_widget.py             ← Base floating widget class
│   ├── clock_widget.py            ← Live clock with seconds arc
│   ├── calendar_widget.py         ← Month calendar, navigable
│   └── monitor_widget.py          ← Live CPU/RAM/disk sparklines
│
├── apps/
│   ├── __init__.py
│   ├── base_app.py                ← BaseApp class all apps inherit
│   ├── registry.py                ← AppRegistry: scan, launch, install
│   ├── calculator/
│   │   ├── manifest.json
│   │   └── main.py                ← Cyberpunk calculator
│   ├── notes/
│   │   ├── manifest.json
│   │   └── main.py                ← Persistent notes app
│   └── color_picker/
│       ├── manifest.json
│       └── main.py                ← RGB/hex color picker
│
├── themes/
│   ├── __init__.py
│   ├── colors.py                  ← Legacy compatibility shim
│   └── theme_engine.py            ← 6 themes, live switching, color proxy
│
├── config/
│   ├── settings.json              ← OS identity, banner, theme, boot config
│   ├── aliases.json               ← User-defined command aliases
│   ├── vx_paths.json              ← Virtual filesystem path map
│   └── history.json               ← Persisted command history (auto-generated)
│
├── vault_storage/                 ← vx://vault — user file storage
├── logs/                          ← vx://logs
└── assets/                        ← vx://grid — future assets
```

---

## All Available Commands

### Built-in Commands

| Command | Description |
|---|---|
| `help` | Show all available commands |
| `clock` | Show current date and time |
| `clock live` | Live ticking clock (Ctrl+C to exit) |
| `clear` | Clear the terminal screen |
| `system` | Show CPU, RAM, OS, architecture |
| `version` | Show VORTEX OS version |
| `whoami` | Show current Linux user identity and groups |
| `exit` / `quit` | Exit VORTEX terminal |

### Filesystem Commands

| Command | Description |
|---|---|
| `vault` | List current directory |
| `vault list <path>` | List any path (supports vx://) |
| `vault go <path>` | Navigate to directory |
| `vault info <path>` | Show file/folder metadata |
| `vault find <name> [path]` | Recursive search by name |
| `vx` | Show VORTEX virtual filesystem map |
| `vx <name>` | Navigate to a vx:// location |
| `vx where` | Show current location as vx:// path |
| `vx resolve <name>` | Show real path of a vx:// name |
| `landmark` | List user landmarks |
| `landmark save <name>` | Save current dir as vx://name |
| `landmark save <name> <path>` | Save specific path as landmark |
| `landmark remove <name>` | Delete a landmark |
| `landmark go <name>` | Navigate to a landmark |

### System Commands

| Command | Description |
|---|---|
| `scan` | System health: RAM, CPU load, disk |
| `scan ports` | Show listening TCP ports |
| `scan network` | Show network interfaces |
| `scan disk` | Show disk usage |
| `ignite` | Show power menu |
| `ignite restart` | Restart the terminal process |
| `ignite shutdown` | Shutdown system (confirmation required) |
| `open browser` | Open default web browser |
| `open <url>` | Open a URL |

### Theme Commands

| Command | Description |
|---|---|
| `theme` | List all themes |
| `theme <name>` | Switch theme (persists to config) |
| `theme preview` | Color swatch of active theme |
| `theme animate` | Cycle all themes with live preview |

### History Commands

| Command | Description |
|---|---|
| `history` | Show last 15 commands |
| `history <n>` | Show last n commands |
| `history clear` | Clear all history |
| `history search <word>` | Filter history by keyword |

### Widget Commands

| Command | Description |
|---|---|
| `clock gui` | Floating live clock widget |
| `calendar` | Floating month calendar |
| `monitor` | Floating system monitor with graphs |
| `widgets` | List all available widgets |
| `desktop` | Show the VORTEX desktop window |
| `reboot` | Replay the boot animation |

### App Commands

| Command | Description |
|---|---|
| `app list` | List all installed apps |
| `app launch <id>` | Launch an app by id |
| `app info <id>` | Show app manifest details |
| `app install <path>` | Register app from folder |
| `app uninstall <id>` | Remove app from registry |

### Tab Terminal

| Command | Description |
|---|---|
| `newtab` | Open new tab in desktop terminal |

---

## Keyboard Shortcuts

### Console Terminal

| Key | Action |
|---|---|
| `↑` / `↓` | Navigate command history |
| `←` / `→` | Move cursor in line |
| `Ctrl+A` | Jump to start of line |
| `Ctrl+E` | Jump to end of line |
| `Ctrl+U` | Clear current line |
| `Ctrl+C` | Interrupt / return to prompt |
| `Ctrl+D` | Exit terminal |

### Desktop Window

| Key | Action |
|---|---|
| `Ctrl+T` | Show terminal (or new tab if open) |
| `Ctrl+W` | Close current terminal tab |
| `Ctrl+Tab` | Next terminal tab |
| `Ctrl+Shift+Tab` | Previous terminal tab |
| `Ctrl+1` to `Ctrl+5` | Jump to tab by number |
| `F11` | Toggle fullscreen |
| `Ctrl+Q` | Hide desktop (console keeps running) |
| `Ctrl+Shift+Q` | Full quit with confirmation |
| `Escape` | Close floating widgets |

---

## Aliases

Defined in `config/aliases.json`. Edit freely — takes effect on next session.

| Alias | Expands to |
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
| `ping` | `scan network` |
| `th` | `theme` |
| `hist` | `history` |
| `cal` | `calendar` |
| `mon` | `monitor` |
| `where` | `vx where` |
| `lm` | `landmark` |
| `goto` | `vx` |
| `launch` | `app launch` |
| `nt` | `newtab` |

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

Switch live: `theme matrix` — persists across restarts.

---

## Virtual Filesystem (vx://)

VORTEX OS uses a virtual path system that maps friendly names to real Ubuntu paths.

| VX Path | Real Path |
|---|---|
| `vx://core` | `~/vortex_os` |
| `vx://home` | `~` |
| `vx://vault` | `~/vortex_os/vault_storage` |
| `vx://config` | `~/vortex_os/config` |
| `vx://grid` | `~/vortex_os/assets` |
| `vx://logs` | `~/vortex_os/logs` |
| `vx://apps` | `~/vortex_os/apps` |
| `vx://widgets` | `~/vortex_os/widgets` |
| `vx://gui` | `~/vortex_os/gui` |
| `vx://tmp` | `/tmp` |
| `vx://root` | `/` |

The shell prompt automatically shows vx:// paths:

```
[VORTEX@CORE vx://core] >
[VORTEX@CORE vx://config] >
[VORTEX@CORE vx://home] >
```

Add your own locations with `landmark save <name>`.

---

## Built-in Apps

| App | ID | Category | Description |
|---|---|---|---|
| VORTEX Calc | `calculator` | tools | Cyberpunk calculator with keyboard support |
| VORTEX Notes | `notes` | productivity | Persistent notes saved to vx://vault |
| VORTEX Colors | `color_picker` | utilities | RGB/hex color picker for theme editing |

Launch from terminal: `app launch calculator`  
Launch from desktop: click `⬡` in sidebar → click app icon

---

## Boot Sequence (Phase 10)

Every startup plays a cinematic boot animation:

```
1. BIOS screen    → real hardware detected and displayed
2. Logo wipe      → ASCII art reveals letter by letter
3. Init messages  → fake-realistic system initialization log
4. Loading bar    → gradient progress bar fills to 100%
5. Flash          → white flash transition
6. Desktop        → fades in and becomes interactive
```

Control via `config/settings.json`:

```json
"boot": {
    "enabled": true,
    "duration_ms": 4500
}
```

Set `"enabled": false` to skip during development.  
Replay anytime with the `reboot` command.

---

## Architecture

### How a command executes

```
python3 main.py
  └── VortexCore.boot()
        ├── BootScreen animation
        └── after boot_complete signal:
              ├── TerminalThread.start()  (QThread)
              └── AppManager.launch_desktop()  (main thread)

User types in console terminal (QThread):
  └── HistoryManager.add()
  └── CommandParser.parse()
        ├── alias expansion
        ├── && chain detection
        └── shlex tokenization → ParsedCommand
              └── CommandRouter.execute()
                    └── handler_function(args, config)
```

### Key Design Patterns

**Registry / Dispatcher** — `CommandRouter` maps names to functions. One `register()` call adds a command.

**Signal / Slot** — All cross-thread GUI operations use Qt signals. The terminal thread never touches GUI objects directly.

**Decorator** — `@with_timestamp` wraps command functions to print execution time without modifying them.

**Proxy** — `_ColorProxy` makes `COLORS.PRIMARY` always return the current theme's color dynamically.

**State Machine** — `BootScreen` progresses through numbered stages driven by `QTimer`.

**Lazy Import** — Apps are loaded at launch time using `importlib.util.spec_from_file_location` so adding a new app requires zero changes to core code.

---

## Configuration Files

### `config/settings.json`
OS identity, banner text, active theme, boot animation settings.

### `config/aliases.json`
User-defined command shortcuts. Edit and restart to apply.

### `config/vx_paths.json`
Virtual filesystem map. Built-in locations and user landmarks.

### `config/history.json`
Auto-generated. Stores up to 500 commands across sessions.

---

## Dependencies

| Package | Purpose | Install |
|---|---|---|
| `colorama` | Terminal colors | `pip3 install colorama` |
| `PyQt6` | GUI desktop, widgets, apps | `pip3 install PyQt6` |

Everything else uses Python's standard library: `os`, `sys`, `json`, `subprocess`, `readline`, `platform`, `datetime`, `shutil`, `shlex`, `grp`, `math`, `collections`, `importlib`.

---

## Development Phases

| Phase | Title | Status |
|---|---|---|
| **1** | Project setup + custom terminal shell | ✅ Complete |
| **2** | Command parser + internal commands + aliases | ✅ Complete |
| **3** | Theme engine + command history + readline | ✅ Complete |
| **4** | Clock + calendar PyQt6 floating widgets | ✅ Complete |
| **5** | PyQt6 desktop environment window | ✅ Complete |
| **6** | System monitor + right-click menu + dock indicators | ✅ Complete |
| **7** | Virtual filesystem + vx:// paths + landmarks | ✅ Complete |
| **8** | Multi-tab terminal | ✅ Complete |
| **9** | App system — registry, manifests, built-in apps, launcher | ✅ Complete |
| **10** | Boot animation + startup screen | ✅ Complete |
| **11** | Login screen | ⏳ Planned |
| **12** | AI assistant integration | ⏳ Planned |
| **13** | Voice assistant | ⏳ Planned |
| **14** | ISO customization | ⏳ Planned |
| **15** | Bootable VORTEX OS image | ⏳ Planned |

---

## Extending VORTEX OS

### Adding a new terminal command

1. Write a function in any `commands/` file:
```python
@with_timestamp
def cmd_mycommand(args, config):
    print("Hello from my command!")
```

2. Import it in `terminal/shell.py`

3. Register it in `_register_commands()`:
```python
"mycommand": (cmd_mycommand, "Does something cool"),
```

Done. Help menu, history, and routing all pick it up automatically.

---

### Adding a new theme

Open `themes/theme_engine.py` and add to the `THEMES` dict:

```python
"mytheme": {
    "name":        "MYTHEME",
    "description": "My custom colors.",
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

### Adding a new app

Create a folder under `apps/` with two files:

**`apps/myapp/manifest.json`**
```json
{
    "id":          "myapp",
    "name":        "My App",
    "version":     "1.0.0",
    "description": "What my app does",
    "entry":       "apps/myapp/main.py",
    "icon":        "◈",
    "category":    "tools",
    "author":      "Hassan Ali Shah"
}
```

**`apps/myapp/main.py`**
```python
from apps.base_app import BaseApp

class MyApp(BaseApp):
    def setup_ui(self):
        pass   # build your UI here

def create_app(manifest):
    return MyApp(manifest)
```

Then `app launch myapp` works. No registration needed — the registry scans automatically.

---

## Known Limitations (Phase 10)

- Per-tab working directories are approximate — `os.chdir()` is global per process
- `open` commands require a running desktop environment
- `ignite shutdown` and `ignite reboot` require sudo privileges
- Startup sound requires PulseAudio to be available
- Autocomplete not yet implemented (planned Phase 11+)

---

## License

MIT License — free to use, modify, and distribute.

---

<div align="center">

---

### Built by **Hassan Ali Shah**
#### [@Hassan_Ali-17](https://github.com/Hassan_Ali-17) on GitHub

---

*No shortcuts. No zip files. Built phase by phase.*

*INITIALIZE. DOMINATE. EVOLVE.*

**VORTEX OS** · Phase 10 of 15 · Codename GENESIS

</div>
