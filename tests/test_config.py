import json

from mouse_battery_tray.config import DEFAULT_CONFIG, load_config, save_config


def test_load_save_config(tmp_path, monkeypatch):
    test_config_file = tmp_path / "config.json"
    monkeypatch.setattr("mouse_battery_tray.config.CONFIG_FILE", str(test_config_file))
    monkeypatch.setattr("mouse_battery_tray.config.CONFIG_DIR", str(tmp_path))

    # Should load default if not exists
    cfg = load_config()
    assert cfg["refresh_interval_sec"] == DEFAULT_CONFIG["refresh_interval_sec"]

    # Save and load
    cfg["refresh_interval_sec"] = 600
    save_config(cfg)

    cfg2 = load_config()
    assert cfg2["refresh_interval_sec"] == 600

def test_corrupted_config(tmp_path, monkeypatch):
    test_config_file = tmp_path / "config.json"
    monkeypatch.setattr("mouse_battery_tray.config.CONFIG_FILE", str(test_config_file))
    monkeypatch.setattr("mouse_battery_tray.config.CONFIG_DIR", str(tmp_path))

    with open(test_config_file, 'w') as f:
        f.write("{ invalid json")

    cfg = load_config()
    assert cfg["refresh_interval_sec"] == DEFAULT_CONFIG["refresh_interval_sec"]

def test_config_merging(tmp_path, monkeypatch):
    test_config_file = tmp_path / "config.json"
    monkeypatch.setattr("mouse_battery_tray.config.CONFIG_FILE", str(test_config_file))
    monkeypatch.setattr("mouse_battery_tray.config.CONFIG_DIR", str(tmp_path))
    
    old_cfg = {
        "refresh_interval_sec": 450,
    }
    with open(test_config_file, 'w', encoding='utf-8') as f:
        json.dump(old_cfg, f)
        
    cfg = load_config()
    assert cfg["refresh_interval_sec"] == 450
    assert "low_battery_threshold" in cfg # check merged default

