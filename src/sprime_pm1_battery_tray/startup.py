import os
import sys
import winreg


APP_NAME = "Mouse Battery Tray"
LEGACY_APP_NAME = "SPRIME PM1 Battery Tray"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
LEGACY_SHORTCUT_NAME = f"{LEGACY_APP_NAME}.lnk"


def _startup_dir():
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def _launch_command():
    if getattr(sys, "frozen", False):
        return f'"{os.path.abspath(sys.executable)}"'

    script_path = os.path.abspath(sys.argv[0])
    python_path = os.path.abspath(sys.executable)
    if python_path.lower().endswith("python.exe"):
        candidate = python_path[:-10] + "pythonw.exe"
        if os.path.isfile(candidate):
            python_path = candidate
    return f'"{python_path}" "{script_path}"'


def _remove_legacy_entries():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, LEGACY_APP_NAME)
            except OSError:
                pass
    except OSError:
        pass

    legacy_shortcut = os.path.join(_startup_dir(), LEGACY_SHORTCUT_NAME)
    try:
        os.remove(legacy_shortcut)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def is_startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except OSError:
        return False


def set_startup(enable):
    if enable:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _launch_command())
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except OSError:
                    pass
        except OSError:
            pass

    _remove_legacy_entries()
