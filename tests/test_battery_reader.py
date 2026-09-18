from mouse_battery_tray import battery_reader


def test_reader_prefers_attack_shark_when_present(monkeypatch):
    monkeypatch.setattr(
        battery_reader.attack_shark,
        "get_battery_info",
        lambda: {"status": "connected", "device": "ATTACK SHARK X1", "battery": 90},
    )
    monkeypatch.setattr(
        battery_reader.hid_protocol,
        "get_battery_info",
        lambda: (_ for _ in ()).throw(AssertionError("PM1 should not be queried")),
    )

    assert battery_reader.get_battery_info()["device"] == "ATTACK SHARK X1"


def test_reader_falls_back_to_pm1(monkeypatch):
    monkeypatch.setattr(
        battery_reader.attack_shark,
        "get_battery_info",
        lambda: {"status": "device_not_found"},
    )
    monkeypatch.setattr(
        battery_reader.hid_protocol,
        "get_battery_info",
        lambda: {"status": "connected", "battery": 77, "charging": False, "full": False},
    )

    result = battery_reader.get_battery_info()

    assert result["device"] == "SPRIME PM1"
    assert result["battery"] == 77


def test_reader_reports_no_supported_mouse(monkeypatch):
    monkeypatch.setattr(
        battery_reader.attack_shark,
        "get_battery_info",
        lambda: {"status": "device_not_found"},
    )
    monkeypatch.setattr(
        battery_reader.hid_protocol,
        "get_battery_info",
        lambda: {"status": "device_not_found"},
    )

    assert battery_reader.get_battery_info() == {"status": "device_not_found", "device": "Mouse"}
