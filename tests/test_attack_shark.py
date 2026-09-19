from __future__ import annotations

from mouse_battery_tray import attack_shark


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

def test_select_battery_endpoint_uses_vendor_usage_fallback_and_rejects_others():
    fallback = {"interface_number": 2, "usage_page": 0xFF10, "path": b"fallback"}
    unrelated = {"interface_number": 1, "usage_page": 0x0A, "path": b"other"}

    assert attack_shark.select_battery_endpoint([unrelated, fallback]) is fallback
    assert attack_shark.select_battery_endpoint([unrelated]) is None


def test_parse_rejects_invalid_values_and_uses_generic_device_name():
    assert attack_shark.parse_battery_packet([0x03, object(), 0x40, 0x01, 50]) is None
    assert attack_shark.parse_battery_packet([0x03, 0xB1, 0x40, 0x01, 101]) is None

    result = attack_shark.parse_battery_packet([0x03, 0xFE, 0x40, 0x03, 100])
    assert result["device"] == "ATTACK SHARK Mouse"
    assert result["charging"] is True
    assert result["full"] is True


def test_read_battery_rejects_missing_path():
    result = attack_shark.read_battery(None)

    assert result["status"] == "protocol_unknown"
    assert "no HID path" in result["error"]


def test_read_battery_classifies_read_failure(monkeypatch):
    closed = []

    class FakeHandle:
        def open_path(self, _path):
            pass

        def set_nonblocking(self, _value):
            pass

        def read(self, _length):
            raise OSError("receiver read failed")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(attack_shark.hid, "device", FakeHandle)

    result = attack_shark.read_battery(b"x1", timeout_sec=1)

    assert result["status"] == "read_failed"
    assert "receiver read failed" in result["error"]
    assert closed


def test_read_battery_timeout_is_sleeping_not_error(monkeypatch):
    class FakeHandle:
        def open_path(self, _path):
            pass

        def set_nonblocking(self, _value):
            pass

        def close(self):
            pass

    monkeypatch.setattr(attack_shark.hid, "device", FakeHandle)

    result = attack_shark.read_battery(b"x1", timeout_sec=0)

    assert result == {
        "status": "disconnected",
        "device": "ATTACK SHARK X1",
        "battery": "--",
        "charging": False,
        "full": False,
    }


def test_get_battery_info_classifies_enumeration_failure(monkeypatch):
    def fail_scan():
        raise OSError("enumeration failed")

    monkeypatch.setattr(attack_shark, "scan_devices", fail_scan)

    result = attack_shark.get_battery_info()

    assert result["status"] == "enumeration_failed"
    assert "enumeration failed" in result["error"]


def test_get_battery_info_reports_missing_receiver(monkeypatch):
    monkeypatch.setattr(attack_shark, "scan_devices", lambda: [])

    assert attack_shark.get_battery_info() == {"status": "device_not_found"}


def test_get_battery_info_reports_unknown_endpoint(monkeypatch):
    monkeypatch.setattr(
        attack_shark,
        "scan_devices",
        lambda: [{"interface_number": 1, "usage_page": 0x01, "path": b"other"}],
    )

    result = attack_shark.get_battery_info()

    assert result["status"] == "protocol_unknown"
    assert "compatible ATTACK SHARK battery endpoint" in result["error"]
