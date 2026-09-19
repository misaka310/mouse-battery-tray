from mouse_battery_tray import battery_reader


def test_reader_returns_attack_shark_result(monkeypatch):
    monkeypatch.setattr(
        battery_reader.attack_shark,
        "get_battery_info",
        lambda: {"status": "connected", "device": "ATTACK SHARK X1", "battery": 90},
    )

    result = battery_reader.get_battery_info()

    assert result["device"] == "ATTACK SHARK X1"
    assert result["battery"] == 90


def test_reader_reports_no_supported_mouse(monkeypatch):
    monkeypatch.setattr(
        battery_reader.attack_shark,
        "get_battery_info",
        lambda: {"status": "device_not_found"},
    )

    assert battery_reader.get_battery_info() == {"status": "device_not_found", "device": "Mouse"}
