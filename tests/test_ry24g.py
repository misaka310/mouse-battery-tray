from __future__ import annotations

from mouse_battery_tray import ry24g


def reply(*, online: bool, level: int = 97, can_read: int = 1) -> list[int]:
    """HIDAPI report ID 0 + 64-byte 0xF7 response."""
    return [0, can_read, 0, level, 1, 0 if online else 1, 1] + [0] * 58


def test_parse_connected_battery_uses_correct_report_offsets():
    result = ry24g.parse_status(reply(online=True, level=54))
    assert result == {
        "device": ry24g.DEVICE_LABEL,
        "status": "connected",
        "battery": 54,
        "charging": False,
        "full": False,
        "source": "ry24g_feature_status",
    }


def test_offline_receiver_never_promotes_cached_level():
    # Observed on DESK2: 00 00 61 01 01 01 after report ID 0.
    result = ry24g.parse_status(reply(online=False, level=97, can_read=0))
    assert result is not None
    assert result["status"] == "disconnected"
    assert result["battery"] == "--"
    assert result["last_reported_battery"] == 97
    assert result["charging"] is False
    assert result["full"] is False


def test_parse_rejects_wrong_length_report_id_flags_and_percentage():
    valid = reply(online=True)
    assert len(valid) == ry24g.FEATURE_WIRE_SIZE
    assert ry24g.parse_status(valid[:-1]) is None
    assert ry24g.parse_status([1] + valid[1:]) is None
    assert ry24g.parse_status([0, 2] + valid[2:]) is None
    assert ry24g.parse_status(valid[:5] + [3] + valid[6:]) is None
    assert ry24g.parse_status(valid[:3] + [101] + valid[4:]) is None


def test_receiver_query_sends_only_read_only_f7_status(monkeypatch):
    called = []

    class Handle:
        def open_path(self, path):
            called.append(("open", path))

        def send_feature_report(self, packet):
            called.append(("send", bytes(packet)))
            return len(packet)

        def get_feature_report(self, rid, length):
            called.append(("get", rid, length))
            return reply(online=True, level=82)

        def close(self):
            called.append(("close",))

    monkeypatch.setattr(ry24g.hid, "device", Handle)
    monkeypatch.setattr(ry24g.time, "sleep", lambda _: None)
    result = ry24g.read_battery(b"test-receiver")
    assert result["status"] == "connected"
    assert result["battery"] == 82
    assert result["receiver_id"].startswith("ry24g-")
    packets = [entry[1] for entry in called if entry[0] == "send"]
    assert packets == [bytes([0, 0xF7] + [0] * 63)]
    assert ("get", 0, 65) in called
    assert called[-1] == ("close",)


def test_read_battery_invalid_reply_and_error_paths(monkeypatch):
    assert ry24g.read_battery(None)["status"] == "protocol_unknown"

    class Handle:
        def open_path(self, path):
            pass

        def send_feature_report(self, payload):
            return 0

        def close(self):
            pass

    monkeypatch.setattr(ry24g.hid, "device", Handle)
    assert ry24g.read_battery(b"receiver")["status"] == "read_failed"

    class BrokenHandle(Handle):
        def send_feature_report(self, payload):
            return len(payload)

        def get_feature_report(self, rid, length):
            return [0, 0]

    monkeypatch.setattr(ry24g.hid, "device", BrokenHandle)
    monkeypatch.setattr(ry24g.time, "sleep", lambda _: None)
    assert ry24g.read_battery(b"receiver")["status"] == "protocol_unknown"

    class DeniedHandle(Handle):
        def open_path(self, path):
            raise OSError("Access denied opening HID")

    monkeypatch.setattr(ry24g.hid, "device", DeniedHandle)
    assert ry24g.read_battery(b"receiver")["status"] == "permission_or_access_error"


def test_enumerate_only_vendor_collection_and_distinct_physical_paths(monkeypatch):
    rows = [
        {"vendor_id": 0x3151, "product_id": 0x5031, "interface_number": 2,
         "usage_page": 0xFFFF, "usage": 2, "path": b"receiver-A"},
        {"vendor_id": 0x3151, "product_id": 0x5031, "interface_number": 2,
         "usage_page": 0xFFFF, "usage": 2, "path": b"receiver-B"},
        {"vendor_id": 0x3151, "product_id": 0x5031, "interface_number": 1,
         "usage_page": 0xFFFF, "usage": 1, "path": b"ignored"},
    ]
    monkeypatch.setattr(ry24g.hid, "enumerate", lambda vid, pid: rows)
    assert len(ry24g.scan_devices()) == 2
    calls = []
    monkeypatch.setattr(
        ry24g, "read_battery",
        lambda path: calls.append(path) or {"status": "disconnected", "battery": "--"},
    )
    assert len(ry24g.get_battery_infos()) == 2
    assert set(calls) == {b"receiver-A", b"receiver-B"}


def test_enumeration_failure_does_not_invent_battery(monkeypatch):
    def fail():
        raise OSError("USB bus gone")

    monkeypatch.setattr(ry24g, "scan_devices", fail)
    result = ry24g.get_battery_infos()
    assert len(result) == 1
    assert result[0]["status"] == "enumeration_failed"
    assert result[0]["battery"] == "--"
    assert "USB bus gone" in result[0]["error"]
