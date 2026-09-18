import json

from sprime_pm1_battery_tray.config import DEFAULT_CONFIG, load_config, save_config


def configure_paths(monkeypatch, tmp_path):
    current_dir = tmp_path / "MouseBatteryTray"
    legacy_dir = tmp_path / "SprimePM1BatteryTray"
    monkeypatch.setattr("sprime_pm1_battery_tray.config.CONFIG_DIR", str(current_dir))
    monkeypatch.setattr(
        "sprime_pm1_battery_tray.config.CONFIG_FILE",
        str(current_dir / "config.json"),
    )
    monkeypatch.setattr(
        "sprime_pm1_battery_tray.config.LEGACY_CONFIG_FILE",
        str(legacy_dir / "config.json"),
    )
    return current_dir, legacy_dir


def test_load_save_config(tmp_path, monkeypatch):
    current_dir, _ = configure_paths(monkeypatch, tmp_path)

    config = load_config()
    assert config["refresh_interval_sec"] == DEFAULT_CONFIG["refresh_interval_sec"]
    assert config["preferred_device"] == "auto"

    config["refresh_interval_sec"] = 600
    config["preferred_device"] = "attack_shark_x1"
    save_config(config)

    loaded = load_config()
    assert loaded["refresh_interval_sec"] == 600
    assert loaded["preferred_device"] == "attack_shark_x1"
    assert (current_dir / "config.json").is_file()


def test_corrupted_config_uses_defaults(tmp_path, monkeypatch):
    current_dir, _ = configure_paths(monkeypatch, tmp_path)
    current_dir.mkdir(parents=True)
    (current_dir / "config.json").write_text("{ invalid json", encoding="utf-8")

    config = load_config()
    assert config["refresh_interval_sec"] == DEFAULT_CONFIG["refresh_interval_sec"]


def test_config_merging_adds_new_keys(tmp_path, monkeypatch):
    current_dir, _ = configure_paths(monkeypatch, tmp_path)
    current_dir.mkdir(parents=True)
    (current_dir / "config.json").write_text(
        json.dumps({"refresh_interval_sec": 450}),
        encoding="utf-8",
    )

    config = load_config()
    assert config["refresh_interval_sec"] == 450
    assert config["preferred_device"] == "auto"
    assert config["config_version"] == 4


def test_legacy_pm1_config_is_migrated_without_deleting_source(tmp_path, monkeypatch):
    current_dir, legacy_dir = configure_paths(monkeypatch, tmp_path)
    legacy_dir.mkdir(parents=True)
    legacy_file = legacy_dir / "config.json"
    legacy_file.write_text(
        json.dumps({"refresh_interval_sec": 120, "start_on_boot": True}),
        encoding="utf-8",
    )

    config = load_config()

    assert config["refresh_interval_sec"] == 120
    assert config["start_on_boot"] is True
    assert config["preferred_device"] == "auto"
    assert legacy_file.is_file()
    assert (current_dir / "config.json").is_file()


def test_invalid_preference_falls_back_to_auto(tmp_path, monkeypatch):
    current_dir, _ = configure_paths(monkeypatch, tmp_path)
    current_dir.mkdir(parents=True)
    (current_dir / "config.json").write_text(
        json.dumps({"preferred_device": "not-a-device"}),
        encoding="utf-8",
    )

    assert load_config()["preferred_device"] == "auto"
