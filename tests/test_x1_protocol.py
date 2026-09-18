from __future__ import annotations

from sprime_pm1_battery_tray import x1_protocol


def endpoint(path=b"device", *, pid=x1_protocol.WIRELESS_PID, interface=2, usage_page=10):
    return {
        "path": path,
        "vendor_id": x1_protocol.VID,
        "product_id": pid,
        "interface_number": interface,
        "usage_page": usage_page,
    }


def test_parse_standard_beken_packet():
    result = x1_protocol.parse_battery_packet([0x03, 0x55, 0x40, 0x01, 73, 0, 0, 0])
    assert result is not None
    assert result["battery"] == 73
    assert result["charging"] is False
    assert result["device_key"] == "attack_shark_x1"


def test_parse_charging_packet():
    result = x1_protocol.parse_battery_packet([0x03, 0x55, 0x40, 0x02, 88, 0, 0, 0])
    assert result is not None
    assert result["battery"] == 88
    assert result["charging"] is True


def test_parse_fallback_packet_shape():
    result = x1_protocol.parse_battery_packet([0x03, 0x55, 42, 0x01, 0xFF])
    assert result is not None
    assert result["battery"] == 42


def test_parse_rejects_non_battery_or_invalid_value():
    assert x1_protocol.parse_battery_packet([0x02, 0x55, 0x40, 0x01, 50]) is None
    assert x1_protocol.parse_battery_packet([0x03, 0x55, 0x40, 0x01, 255]) is None


def test_select_wireless_endpoint_prefers_interface2_usage10():
    devices = [
        endpoint(b"fallback", interface=1, usage_page=1),
        endpoint(b"private", interface=2, usage_page=0xFF00),
        endpoint(b"best", interface=2, usage_page=10),
    ]
    assert x1_protocol.select_wireless_endpoint(devices)["path"] == b"best"


def test_reader_returns_live_battery_and_keeps_handle(monkeypatch):
    class FakeHandle:
        def __init__(self):
            self.closed = False

        def open_path(self, path):
            assert path == b"wireless"

        def set_nonblocking(self, value):
            assert value is True

        def read(self, _length):
            return [0x03, 0x55, 0x40, 0x01, 61, 0, 0, 0]

        def close(self):
            self.closed = True

    handle = FakeHandle()
    monkeypatch.setattr(x1_protocol, "scan_devices", lambda: [endpoint(b"wireless")])
    monkeypatch.setattr(x1_protocol.hid, "device", lambda: handle)

    reader = x1_protocol.X1BatteryReader()
    result = reader.read(timeout_sec=0)

    assert result["status"] == "connected"
    assert result["battery"] == 61
    assert reader._handle is handle
    reader.close()
    assert handle.closed is True


def test_reader_reports_wired_without_fake_percentage(monkeypatch):
    monkeypatch.setattr(
        x1_protocol,
        "scan_devices",
        lambda: [endpoint(b"wired", pid=x1_protocol.WIRED_PID)],
    )

    result = x1_protocol.X1BatteryReader().read(timeout_sec=0)

    assert result["status"] == "connected"
    assert result["battery"] is None
    assert result["charging"] is True


def test_reader_reports_missing_receiver(monkeypatch):
    monkeypatch.setattr(x1_protocol, "scan_devices", lambda: [])
    result = x1_protocol.X1BatteryReader().read(timeout_sec=0)
    assert result["status"] == "device_not_found"
    assert result["recommended_refresh_sec"] == 5
