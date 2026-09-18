from __future__ import annotations

import os
import sys
import winreg

APP_NAME = "Mouse Battery Tray"
RUN_VALUE_NAME = "MouseBatteryTray"
LEGACY_RUN_VALUE_NAMES = ("SPRIME PM1 Battery Tray",)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
LEGACY_SHORTCUT_NAMES = ("SPRIME PM1 Battery Tray.lnk",)


def _startup_dir():
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def _launch_command():
    if getattr(sys, "frozen", False):
        return f'"{os.path.abspath(sys.executable)}"'

    script_path = os.path.abspath(sys.argv[0])
    pythonw = sys.executable
    if pythonw.lower().endswith("python.exe"):
        candidate = pythonw[:-10] + "pythonw.exe"
        if os.path.exists(candidate):
            pythonw = candidate
    return f'"{os.path.abspath(pythonw)}" "{script_path}"'


def _delete_run_value(name):
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, name)
    except OSError:
        pass


def _remove_legacy_startup_shortcuts():
    for name in LEGACY_SHORTCUT_NAMES:
        try:
            os.remove(os.path.join(_startup_dir(), name))
        except FileNotFoundError:
            pass
        except OSError:
            pass


def is_startup_enabled():
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, RUN_VALUE_NAME)
        return bool(value)
    except OSError:
        return False


def set_startup(enable):
    if enable:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, _launch_command())
    else:
        _delete_run_value(RUN_VALUE_NAME)

    for name in LEGACY_RUN_VALUE_NAMES:
        _delete_run_value(name)
    _remove_legacy_startup_shortcuts()
