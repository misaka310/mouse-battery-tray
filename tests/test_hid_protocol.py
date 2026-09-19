from __future__ import annotations

import pytest

from mouse_battery_tray import hid_protocol
from mouse_battery_tray.hid_protocol import (
    get_battery_info,
    parse_battery_report,
    read_battery,
    select_sprime_device,
)


def test_parse_connected_battery_report():
    report = [0] * 32
    report[9] = 96
    report[10] = 0
    report[11] = 0
    report[12] = 1

    res = parse_battery_report(report)

    assert res == {
        "status": "connected",
        "battery": 96,
        "charging": False,
        "full": False,
    }


def test_parse_charging_full_battery_report():
    report = [0] * 32
    report[9] = 100
    report[10] = 1
    report[11] = 1
    report[12] = 1

    res = parse_battery_report(report)

    assert res["status"] == "connected"
    assert res["battery"] == 100
    assert res["charging"] is True
    assert res["full"] is True


def test_parse_disconnected_battery_report():
    report = [0] * 32
    report[9] = 55
    report[12] = 0

    res = parse_battery_report(report)

    assert res["status"] == "disconnected"
    assert res["battery"] == 55


def test_parse_invalid_response_length():
    res = parse_battery_report([0] * 8)

    assert res["status"] == "read_failed"
    assert "Invalid response length" in res["error"]


@pytest.mark.parametrize("battery", [-1, 101, 255])
def test_parse_rejects_out_of_range_battery(battery):
    report = [0] * 32
    report[9] = battery
    report[12] = 1

    res = parse_battery_report(report)

    assert res["status"] == "invalid_report"
    assert str(battery) in res["error"]


def test_parse_rejects_non_boolean_flags():
    report = [0] * 32
    report[9] = 50
    report[10] = 2
    report[12] = 1

    res = parse_battery_report(report)

    assert res["status"] == "invalid_report"
    assert "charging=2" in res["error"]


def test_select_sprime_device_prefers_col04_case_insensitively():
    devices = [
        {"path": b"\\\\?\\hid#vid_1915&pid_ac1c&mi_01&col02"},
        {"path": b"\\\\?\\hid#vid_1915&pid_ac1c&mi_01&Col04"},
    ]

    selected = select_sprime_device(devices)

    assert selected is devices[1]


def test_query_feature_report_rejects_failed_send_and_closes(monkeypatch):
    calls = []

    class FakeHandle:
        def open_path(self, device_path):
            calls.append(("open", device_path))

        def set_nonblocking(self, value):
            calls.append(("nonblocking", value))

        def send_feature_report(self, _buf):
            return 0

        def get_feature_report(self, _report_id, _length):
            raise AssertionError("get_feature_report should not be called")

        def close(self):
            calls.append(("close", None))

    monkeypatch.setattr(hid_protocol.hid, "device", FakeHandle)

    with pytest.raises(hid_protocol.SprimeDeviceError, match="not accepted"):
        hid_protocol._query_feature_report(b"device")

    assert calls[-1][0] == "close"


def test_read_battery_classifies_access_errors(monkeypatch):
    monkeypatch.setattr(
        hid_protocol,
        "_query_feature_report",
        lambda _path: (_ for _ in ()).throw(OSError("access denied while opening HID")),
    )

    result = read_battery(b"device")

    assert result["status"] == "permission_or_access_error"
    assert "access denied" in result["error"]


def test_get_battery_info_reports_enumeration_failure(monkeypatch):
    monkeypatch.setattr(
        hid_protocol,
        "scan_devices",
        lambda: (_ for _ in ()).throw(RuntimeError("enumeration failed")),
    )

    result = get_battery_info()

    assert result == {"status": "enumeration_failed", "error": "enumeration failed"}


def test_select_sprime_device_continues_after_probe_exception(monkeypatch):
    devices = [{"path": b"first"}, {"path": b"second"}]
    responses = iter([OSError("busy"), [0] * 32])

    def fake_query(_path):
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(hid_protocol, "_query_feature_report", fake_query)

    assert select_sprime_device(devices) is devices[1]
