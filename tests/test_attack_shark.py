from __future__ import annotations

from sprime_pm1_battery_tray import attack_shark


def test_parse_verified_x1_packet():
    result = attack_shark.parse_battery_packet([0x03, 0xB1, 0x40, 0x01, 0x5A])

    assert result == {
        "status": "connected",
        "device": "ATTACK SHARK X1",
        "battery": 90,
        "charging": False,
        "full": False,
        "device_id": 0xB1,
    }


def test_parse_charging_packet_and_x6_scale():
    result = attack_shark.parse_battery_packet([0x03, 0x85, 0x40, 0x02, 0x08])

    assert result["device"] == "ATTACK SHARK X6"
    assert result["battery"] == 80
    assert result["charging"] is True


def test_parse_rejects_unrelated_packet():
    assert attack_shark.parse_battery_packet([0x02, 0xB1, 0x40, 0x01, 90]) is None
    assert attack_shark.parse_battery_packet([0x03, 0xB1, 0x41, 0x01, 90]) is None
    assert attack_shark.parse_battery_packet([0x03, 0xB1]) is None


def test_select_battery_endpoint_prefers_verified_usage_page():
    fallback = {"interface_number": 2, "usage_page": 0xFF00, "path": b"fallback"}
    verified = {"interface_number": 2, "usage_page": 0x0A, "path": b"x1"}

    assert attack_shark.select_battery_endpoint([fallback, verified]) is verified


def test_read_battery_reads_passive_heartbeat(monkeypatch):
    calls = []

    class FakeHandle:
        def open_path(self, path):
            calls.append(("open", path))

        def set_nonblocking(self, value):
            calls.append(("nonblocking", value))

        def read(self, length):
            calls.append(("read", length))
            return [0x03, 0xB1, 0x40, 0x01, 0x5A]

        def close(self):
            calls.append(("close",))

    monkeypatch.setattr(attack_shark.hid, "device", FakeHandle)

    result = attack_shark.read_battery(b"x1", timeout_sec=1)

    assert result["device"] == "ATTACK SHARK X1"
    assert result["battery"] == 90
    assert calls[-1] == ("close",)


def test_read_battery_classifies_access_error(monkeypatch):
    class FakeHandle:
        def open_path(self, _path):
            raise OSError("access denied opening HID")

        def close(self):
            pass

    monkeypatch.setattr(attack_shark.hid, "device", FakeHandle)

    result = attack_shark.read_battery(b"x1")

    assert result["status"] == "permission_or_access_error"
    assert "access denied" in result["error"]


def test_get_battery_info_reports_sleeping_receiver(monkeypatch):
    monkeypatch.setattr(
        attack_shark,
        "scan_devices",
        lambda: [{"interface_number": 2, "usage_page": 0x0A, "path": b"x1"}],
    )
    monkeypatch.setattr(
        attack_shark,
        "read_battery",
        lambda _path, timeout_sec=5.0: {
            "status": "disconnected",
            "device": "ATTACK SHARK X1",
            "battery": "--",
            "charging": False,
            "full": False,
        },
    )

    result = attack_shark.get_battery_info()

    assert result["status"] == "disconnected"
    assert result["device"] == "ATTACK SHARK X1"
