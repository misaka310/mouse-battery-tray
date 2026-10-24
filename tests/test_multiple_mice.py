from __future__ import annotations

from mouse_battery_tray import attack_shark, battery_reader


def test_distinct_receivers_are_read_independently(monkeypatch):
    dongles = [
        {"interface_number": 2, "usage_page": 0x0A, "path": b"HID&mi_02&col01#first"},
        {"interface_number": 2, "usage_page": 0xFF00, "path": b"HID&mi_02&col03#first"},
        {"interface_number": 2, "usage_page": 0x0A, "path": b"HID&mi_02&col01#second"},
    ]
    monkeypatch.setattr(attack_shark, "scan_devices", lambda: dongles)
    calls = []

    def read(path, timeout_sec=5.0):
        calls.append(path)
        return {
            "status": "connected", "device": "ATTACK SHARK X1",
            "battery": 80 if b"first" in path else 30,
            "charging": False, "full": False,
        }

    monkeypatch.setattr(attack_shark, "read_battery", read)
    results = attack_shark.get_battery_infos()
    assert len(results) == 2
    assert len(set(item["receiver_id"] for item in results)) == 2
    assert {item["battery"] for item in results} == {80, 30}
    assert all(" #" in item["label"] for item in results)
    assert len(calls) == 2


def test_monitor_combines_m575_and_x1(monkeypatch):
    monkeypatch.setattr(
        battery_reader.attack_shark, "get_battery_infos",
        lambda: [{"status": "connected", "device": "ATTACK SHARK X1",
                  "battery": 90, "charging": False, "receiver_id": "x1-A"}],
    )
    from mouse_battery_tray import bluetooth_m575
    monkeypatch.setattr(
        bluetooth_m575, "get_battery_infos",
        lambda: [{"status": "connected", "device": "Logitech ERGO M575",
                  "battery": 75, "charging": False, "receiver_id": "bt-B"}],
    )
    result = battery_reader.get_monitor_info()
    assert result["status"] == "connected"
    assert result["battery"] == 75
    assert len(result["devices"]) == 2


def test_monitor_clears_stale_battery_when_absent(monkeypatch):
    from mouse_battery_tray import bluetooth_m575
    monkeypatch.setattr(battery_reader.attack_shark, "get_battery_infos", lambda: [])
    monkeypatch.setattr(bluetooth_m575, "get_battery_infos", lambda: [])
    assert battery_reader.get_monitor_info() == {
        "status": "device_not_found", "device": "Mouse", "battery": "--",
        "charging": False, "full": False, "devices": [],
    }


def test_monitor_shows_sleeping_receiver_without_fake_percent(monkeypatch):
    from mouse_battery_tray import bluetooth_m575
    monkeypatch.setattr(
        battery_reader.attack_shark, "get_battery_infos",
        lambda: [{"status": "disconnected", "device": "ATTACK SHARK X1",
                  "battery": "--", "receiver_id": "x1-A"}],
    )
    monkeypatch.setattr(bluetooth_m575, "get_battery_infos", lambda: [])
    result = battery_reader.get_monitor_info()
    assert result["status"] == "disconnected"
    assert result["battery"] == "--"
    assert len(result["devices"]) == 1
