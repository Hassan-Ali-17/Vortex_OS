# commands/ai_commands.py
# VORTEX OS - AI assistant terminal commands

from themes.colors import COLORS
from commands.builtin_commands import with_timestamp


@with_timestamp
def cmd_aria(args, config):
    """
    Command: aria [question]

    Opens the ARIA AI panel on the desktop.
    If a question is provided, pre-fills it.

    Examples:
        aria                        → opens AI panel
        aria how do I list files    → opens panel with question
        aria explain the vx command → pre-filled question
    """
    from core.app_manager import get_app_manager
    from PyQt6.QtCore     import QTimer
    manager = get_app_manager()

    if manager is None or manager._desktop is None:
        print(f"\n{COLORS.ERROR}  [!] Desktop not available. "
              f"Type 'desktop' first.{COLORS.RESET}\n")
        return

    # Pre-fill question if provided
    question = " ".join(args).strip() if args else ""

    def _open_aria():
        desktop = manager._desktop
        if not desktop.isVisible():
            desktop.show()

        # Show the AI panel
        if hasattr(desktop, 'ai_panel'):
            desktop.ai_panel.toggle()

            # Pre-fill question after panel slides in
            if question:
                def _prefill():
                    desktop.ai_panel.input_line.setText(question)
                    desktop.ai_panel.input_line.setFocus()
                QTimer.singleShot(350, _prefill)

    QTimer.singleShot(100, _open_aria)

    print(f"\n{COLORS.ACCENT}  ◈ ARIA panel requested.{COLORS.RESET}\n")