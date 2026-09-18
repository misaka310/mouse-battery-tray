import json
import os
import sys


APP_DATA_DIR_NAME = "MouseBatteryTray"
LEGACY_APP_DATA_DIR_NAME = "SprimePM1BatteryTray"


def _data_base():
    return os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")


def _get_application_data_root():
    return os.path.abspath(os.path.join(_data_base(), APP_DATA_DIR_NAME))


def _get_legacy_config_file():
    return os.path.abspath(os.path.join(_data_base(), LEGACY_APP_DATA_DIR_NAME, "config.json"))


def _get_application_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


CONFIG_DIR = _get_application_data_root()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "config_version": 4,
    "refresh_interval_sec": 300,
    "low_battery_threshold": 20,
    "notify_low_battery": True,
    "start_on_boot": False,
}


def get_log_dir():
    return os.path.join(_get_application_root(), "logs")


def _read_config(path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg)
    merged["config_version"] = DEFAULT_CONFIG["config_version"]
    return merged


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            return _read_config(CONFIG_FILE)
        except (OSError, ValueError, TypeError):
            return DEFAULT_CONFIG.copy()

    # Only consult the old SPRIME path for the real application path. Tests and
    # alternate callers that monkeypatch CONFIG_FILE should remain isolated.
    if os.path.basename(os.path.dirname(CONFIG_FILE)) == APP_DATA_DIR_NAME:
        legacy_file = _get_legacy_config_file()
        if os.path.exists(legacy_file):
            try:
                migrated = _read_config(legacy_file)
                save_config(migrated)
                return migrated
            except (OSError, ValueError, TypeError):
                pass

    return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    payload = DEFAULT_CONFIG.copy()
    payload.update(config)
    payload["config_version"] = DEFAULT_CONFIG["config_version"]
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)
