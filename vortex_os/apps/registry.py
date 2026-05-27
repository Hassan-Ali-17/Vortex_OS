# apps/registry.py
# VORTEX OS - App Registry
# Scans apps/ folder, loads manifests, launches apps.

import os
import json
import importlib.util


class AppRegistry:
    """
    Central registry for all VORTEX OS applications.

    Lifecycle:
    1. scan()       → finds all app folders with manifest.json
    2. load()       → reads each manifest into memory
    3. launch(id)   → imports the app module, creates instance, shows it

    Why importlib instead of a regular import?
    Regular imports need the module to be on sys.path and known
    at startup. importlib.util.spec_from_file_location() lets us
    load ANY Python file from ANY path at runtime — perfect for
    a plugin-style app system where apps can be added later.
    """

    APPS_DIR = "apps"

    def __init__(self):
        # id → manifest dict
        self._manifests = {}

        # id → live BaseApp instance (if currently open)
        self._instances = {}

        self.scan()

    def scan(self):
        """
        Scans the apps/ directory for valid app folders.

        A valid app folder must contain:
        - manifest.json  (app metadata)
        - main.py        (app entry point)

        Invalid folders are skipped with a warning.
        """
        self._manifests.clear()

        if not os.path.isdir(self.APPS_DIR):
            return

        for entry in os.scandir(self.APPS_DIR):
            if not entry.is_dir():
                continue

            manifest_path = os.path.join(entry.path, "manifest.json")
            main_path     = os.path.join(entry.path, "main.py")

            if not os.path.isfile(manifest_path):
                continue
            if not os.path.isfile(main_path):
                continue

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)

                # Validate required fields
                required = ["id", "name", "version", "entry"]
                missing  = [k for k in required if k not in manifest]
                if missing:
                    print(f"[AppRegistry] Skipping {entry.name}: "
                          f"missing fields {missing}")
                    continue

                app_id = manifest["id"]
                manifest["_path"] = entry.path
                self._manifests[app_id] = manifest

            except json.JSONDecodeError as e:
                print(f"[AppRegistry] Bad manifest in {entry.name}: {e}")
            except Exception as e:
                print(f"[AppRegistry] Error loading {entry.name}: {e}")

    def get_all(self):
        """
        Returns list of all manifest dicts, sorted by name.
        """
        return sorted(
            self._manifests.values(),
            key=lambda m: m.get("name", "")
        )

    def get(self, app_id):
        """Returns manifest for a specific app id, or None."""
        return self._manifests.get(app_id)

    def is_running(self, app_id):
        """Returns True if this app has an open window."""
        inst = self._instances.get(app_id)
        return inst is not None and inst.isVisible()

    def launch(self, app_id):
     """
    Launches an app by id.
    If already running: brings window to front.
    If not: creates instance and shows it.
    """
     manifest = self._manifests.get(app_id)
     if manifest is None:
        return False, f"App '{app_id}' not found."

     # Already open? Just raise it.
     if self.is_running(app_id):
        inst = self._instances[app_id]
        inst.show()
        inst.raise_()
        inst.activateWindow()
        return True, inst

     app_path = os.path.join(manifest["_path"], "main.py")

     try:
        spec   = importlib.util.spec_from_file_location(
                     f"vortex_app_{app_id}", app_path
                 )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, 'create_app'):
            return False, (f"main.py in '{app_id}' missing "
                           f"create_app() function.")

        instance = module.create_app(manifest)
        instance.app_closed.connect(
            lambda aid=app_id: self._on_app_closed(aid)
        )

        # ── Position the app centered on the desktop ──────────
        # Try to get the desktop window from AppManager
        try:
            from core.app_manager import get_app_manager
            manager = get_app_manager()

            if manager and manager._desktop:
                desktop = manager._desktop
                dg      = desktop.geometry()

                # Center the app window over the desktop
                app_w   = instance.width()  or 400
                app_h   = instance.height() or 300
                center_x = dg.x() + (dg.width()  - app_w) // 2
                center_y = dg.y() + (dg.height() - app_h) // 2
                instance.move(center_x, center_y)

        except Exception:
            pass   # Centering is cosmetic — never block launch

        instance.on_launch()
        instance.show()
        instance.raise_()
        instance.activateWindow()

        self._instances[app_id] = instance
        return True, instance

     except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)

    def close_app(self, app_id):
        """Hides and cleans up a running app."""
        inst = self._instances.get(app_id)
        if inst:
            inst.hide()

    def _on_app_closed(self, app_id):
        """Called when an app emits app_closed signal."""
        if app_id in self._instances:
            del self._instances[app_id]

    def install(self, folder_path):
        """
        Registers an app from an external folder path.
        Copies nothing — just validates and adds to registry.

        Returns:
            (True,  app_id) on success
            (False, reason) on failure
        """
        folder_path    = os.path.expanduser(folder_path)
        manifest_path  = os.path.join(folder_path, "manifest.json")
        main_path      = os.path.join(folder_path, "main.py")

        if not os.path.isdir(folder_path):
            return False, "Folder not found."
        if not os.path.isfile(manifest_path):
            return False, "No manifest.json found."
        if not os.path.isfile(main_path):
            return False, "No main.py found."

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            app_id             = manifest["id"]
            manifest["_path"]  = folder_path
            self._manifests[app_id] = manifest
            return True, app_id
        except Exception as e:
            return False, str(e)

    def uninstall(self, app_id):
        """
        Removes an app from the registry.
        Does NOT delete files — just removes from memory.

        Returns:
            (True,  app_id) on success
            (False, reason) on failure
        """
        if app_id not in self._manifests:
            return False, f"App '{app_id}' not found."

        # Close if running
        self.close_app(app_id)

        del self._manifests[app_id]
        return True, app_id


# ── Global singleton ──────────────────────────────────────

_registry = None


def get_registry():
    """Returns the global AppRegistry instance."""
    global _registry
    if _registry is None:
        _registry = AppRegistry()
    return _registry