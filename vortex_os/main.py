# main.py
# VORTEX OS - Entry Point
# Run this file to start VORTEX OS.
# Usage: python3 main.py

import os
import sys

# Add the project root to Python's path
# This ensures all imports work no matter where you run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.vortex_core import launch


if __name__ == "__main__":
    # __name__ == "__main__" means this file was run directly,
    # not imported by another file. This is standard Python practice.
    launch()