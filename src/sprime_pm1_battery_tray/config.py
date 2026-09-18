import json
import os
import sys


def _get_application_data_root():
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.abspath(os.path.join(base, "MouseBatteryTray"))


def _get_legacy_application_data_root():
    base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.abspath(os.path.join(base, "SprimePM1BatteryTray"))


def _get_application_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


CONFIG_DIR = _get_application_data_root()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LEGACY_CONFIG_FILE = os.path.join(_get_legacy_application_data_root(), "config.json")

DEFAULT_CONFIG = {
    "config_version": 4,
    "refresh_interval_sec": 300,
    "low_battery_threshold": 20,
    "notify_low_battery": True,
    "start_on_boot": False,
    "preferred_device": "auto",
}


def get_log_dir():
    return os.path.join(_get_application_root(), "logs")


def _read_config_file(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _merge_config(data):
    merged = DEFAULT_CONFIG.copy()
    if isinstance(data, dict):
        merged.update(data)
    merged["config_version"] = DEFAULT_CONFIG["config_version"]
    if merged.get("preferred_device") not in {"auto", "attack_shark_x1", "sprime_pm1"}:
        merged["preferred_device"] = "auto"
    return merged


def load_config():
    current = _read_config_file(CONFIG_FILE)
    if current is not None:
        return _merge_config(current)

    legacy = _read_config_file(LEGACY_CONFIG_FILE)
    if legacy is not None:
        migrated = _merge_config(legacy)
        try:
            save_config(migrated)
        except OSError:
            pass
        return migrated

    return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    merged = _merge_config(config)
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(merged, file, indent=4)
