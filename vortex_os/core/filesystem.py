# core/filesystem.py
# VORTEX OS - Virtual Filesystem Abstraction Layer
#
# This module is the bridge between VORTEX virtual paths
# and real Ubuntu filesystem paths.
#
# KEY CONCEPTS:
# - "vx path"   : a VORTEX virtual path like 'vx://core' or 'core'
# - "real path" : an actual Ubuntu path like '/home/hassan/vortex_os'
# - "landmark"  : a user-saved named location (like bookmarks)

import os
import json


class VortexFilesystem:
    """
    Manages the VORTEX virtual filesystem.

    Responsibilities:
    - Load and save the vx_paths.json config
    - Resolve vx:// paths to real filesystem paths
    - Translate real paths back to vx:// display names
    - Manage user-defined landmarks
    - Provide directory listings with VORTEX path display
    """

    VX_PREFIX = "vx://"

    def __init__(self, config_path="config/vx_paths.json"):
        self.config_path = config_path
        self._data       = {}      # Raw loaded JSON
        self._locations  = {}      # name → expanded real path
        self._landmarks  = {}      # user-saved name → real path
        self._load()

    # ─────────────────────────────────────────────────────
    #  LOADING AND SAVING
    # ─────────────────────────────────────────────────────

    def _load(self):
        """
        Loads vx_paths.json and expands all ~ in paths.
        If file not found, uses built-in defaults.
        """
        try:
            with open(self.config_path, 'r') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = self._default_data()
        except json.JSONDecodeError as e:
            print(f"[WARN] vx_paths.json malformed: {e}")
            self._data = self._default_data()

        # Expand all ~ to real home directory paths
        raw_locations = self._data.get("locations", {})
        self._locations = {
            name: os.path.expanduser(path)
            for name, path in raw_locations.items()
        }

        raw_landmarks = self._data.get("landmarks", {})
        self._landmarks = {
            name: os.path.expanduser(path)
            for name, path in raw_landmarks.items()
        }

    def _save(self):
        """
        Persists current state back to vx_paths.json.
        Called whenever landmarks change.
        """
        # Convert expanded paths back to ~ form for storage
        home = os.path.expanduser("~")

        def compress(path):
            if path.startswith(home):
                return "~" + path[len(home):]
            return path

        self._data["landmarks"] = {
            name: compress(path)
            for name, path in self._landmarks.items()
        }

        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._data, f, indent=4)
        except Exception as e:
            print(f"[WARN] Could not save vx_paths: {e}")

    def _default_data(self):
        """Fallback data if config file is missing."""
        return {
            "locations": {
                "core":   "~/vortex_os",
                "home":   "~",
                "config": "~/vortex_os/config",
                "tmp":    "/tmp",
            },
            "landmarks": {}
        }

    # ─────────────────────────────────────────────────────
    #  PATH RESOLUTION
    # ─────────────────────────────────────────────────────

    def resolve(self, vx_path):
        """
        Converts a VORTEX path to a real filesystem path.

        Handles these input forms:
            'vx://core'    → '/home/hassan/vortex_os'
            'core'         → '/home/hassan/vortex_os'
            'vx://home'    → '/home/hassan'
            'mylandmark'   → whatever it was saved as
            '/real/path'   → returned as-is (pass-through)
            '~/documents'  → expanded to real path

        Returns:
            str  : real filesystem path
            None : if the vx name is not found

        Why return None instead of raising?
        Commands can then print a friendly error instead of crashing.
        """
        if not vx_path:
            return None

        path = vx_path.strip()

        # Strip vx:// prefix if present
        if path.startswith(self.VX_PREFIX):
            path = path[len(self.VX_PREFIX):]

        # Check built-in locations first
        if path in self._locations:
            return self._locations[path]

        # Then check user landmarks
        if path in self._landmarks:
            return self._landmarks[path]

        # Expand ~ and return as real path
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            return expanded

        # Nothing matched
        return None

    def display_path(self, real_path):
        """
        Converts a real filesystem path to a VORTEX display path.

        This is used in the shell prompt so users see:
            [VORTEX@CORE vx://core] >
        instead of:
            [VORTEX@CORE /home/hassan/vortex_os] >

        Strategy:
        - Check all known locations AND landmarks
        - Find the longest matching prefix (most specific match)
        - Replace that prefix with vx://name

        Example:
            real = '/home/hassan/vortex_os/config'
            locations includes 'core' → '/home/hassan/vortex_os'
                              'config' → '/home/hassan/vortex_os/config'
            'config' is longer match → returns 'vx://config'
        """
        if not real_path:
            return real_path

        # Combine all named locations + landmarks for lookup
        all_named = {**self._locations, **self._landmarks}

        best_name   = None
        best_length = 0

        for name, loc_path in all_named.items():
            # Normalize both paths for comparison
            norm_real = os.path.normpath(real_path)
            norm_loc  = os.path.normpath(loc_path)

            if norm_real == norm_loc:
                # Exact match — use this name directly
                return f"{self.VX_PREFIX}{name}"

            if (norm_real.startswith(norm_loc + os.sep)
                    and len(norm_loc) > best_length):
                best_name   = name
                best_length = len(norm_loc)

        if best_name:
            # Build relative suffix after the matched prefix
            norm_real = os.path.normpath(real_path)
            norm_loc  = os.path.normpath(all_named[best_name])
            suffix    = norm_real[len(norm_loc):]
            return f"{self.VX_PREFIX}{best_name}{suffix}"

        # No match — fall back to ~ compression
        home = os.path.expanduser("~")
        if real_path.startswith(home):
            return "~" + real_path[len(home):]

        return real_path

    # ─────────────────────────────────────────────────────
    #  LANDMARK MANAGEMENT
    # ─────────────────────────────────────────────────────

    def add_landmark(self, name, real_path=None):
        """
        Saves a directory as a named VORTEX landmark.

        Args:
            name      : the vx:// name to assign
            real_path : the path to save (default: current directory)

        Returns:
            (True, real_path)  on success
            (False, reason)    on failure
        """
        # Validate name — only lowercase letters, numbers, underscores
        import re
        if not re.match(r'^[a-z0-9_]+$', name):
            return False, "Name must be lowercase letters, numbers, underscores only."

        # Don't allow overwriting built-in locations
        if name in self._locations:
            return False, f"'{name}' is a built-in location and cannot be overwritten."

        path = real_path or os.getcwd()
        path = os.path.expanduser(path)

        if not os.path.isdir(path):
            return False, f"Path does not exist or is not a directory: {path}"

        self._landmarks[name] = path
        self._save()
        return True, path

    def remove_landmark(self, name):
        """
        Removes a user landmark.

        Returns:
            (True, name)    on success
            (False, reason) on failure
        """
        if name in self._locations:
            return False, f"'{name}' is a built-in location and cannot be removed."

        if name not in self._landmarks:
            return False, f"Landmark '{name}' not found."

        del self._landmarks[name]
        self._save()
        return True, name

    def get_all_locations(self):
        """
        Returns all known locations (built-in + landmarks).

        Returns:
            list of (name, real_path, kind) tuples
            kind is either 'builtin' or 'landmark'
        """
        result = []

        for name, path in sorted(self._locations.items()):
            result.append((name, path, "builtin"))

        for name, path in sorted(self._landmarks.items()):
            result.append((name, path, "landmark"))

        return result

    def exists(self, vx_path):
        """Returns True if the vx path resolves to an existing directory."""
        real = self.resolve(vx_path)
        return real is not None and os.path.exists(real)

    def reload(self):
        """Reloads config from disk. Useful after manual JSON edits."""
        self._load()


# ─────────────────────────────────────────────────────────
#  GLOBAL INSTANCE
#  One VortexFilesystem shared across the whole process.
#  Imported by commands and the shell prompt.
# ─────────────────────────────────────────────────────────

_vfs = None


def get_vfs():
    """Returns the global VortexFilesystem instance."""
    global _vfs
    if _vfs is None:
        _vfs = VortexFilesystem()
    return _vfs