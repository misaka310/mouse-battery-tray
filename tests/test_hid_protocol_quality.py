from __future__ import annotations

from types import SimpleNamespace

import pytest

from mouse_battery_tray import hid_protocol


def test_query_feature_report_builds_command_and_closes(monkeypatch) -> None:
    calls = []
    response = [0] * 32
    response[9] = 80
    response[12] = 1

    class FakeHandle:
        def open_path(self, path):
            calls.append(("open", path))

        def set_nonblocking(self, value):
            calls.append(("nonblocking", value))

        def send_feature_report(self, payload):
            calls.append(("send", bytes(payload)))
            return len(payload)

        def get_feature_report(self, report_id, length):
            calls.append(("get", report_id, length))
            return response

        def close(self):
            calls.append(("close",))

    monkeypatch.setattr(hid_protocol.hid, "device", FakeHandle)
    monkeypatch.setattr(hid_protocol.time, "sleep", lambda _seconds: None)

    assert hid_protocol._query_feature_report(b"device") is response
    command = next(value for name, value in calls if name == "send")
    assert command[0] == hid_protocol.FEATURE_REPORT_ID
    assert command[1] == hid_protocol.QUERY_COMMAND
    assert command[4] == hid_protocol.QUERY_FLAG
    assert calls[-1] == ("close",)


def test_query_feature_report_rejects_missing_path_and_empty_response(monkeypatch) -> None:
    with pytest.raises(hid_protocol.SprimeDeviceError, match="path is required"):
        hid_protocol._query_feature_report(None)

    handle = SimpleNamespace(
        open_path=lambda _path: None,
        set_nonblocking=lambda _value: None,
        send_feature_report=lambda _payload: 32,
        get_feature_report=lambda _report_id, _length: [],
        close=lambda: None,
    )
    monkeypatch.setattr(hid_protocol.hid, "device", lambda: handle)
    monkeypatch.setattr(hid_protocol.time, "sleep", lambda _seconds: None)

    with pytest.raises(hid_protocol.SprimeDeviceError, match="no response"):
        hid_protocol._query_feature_report(b"device")


def test_parse_rejects_values_that_cannot_be_converted() -> None:
    report = [0] * 32
    report[9] = "invalid"
    report[12] = 1

    result = hid_protocol.parse_battery_report(report)

    assert result["status"] == "invalid_report"
    assert "Invalid report values" in result["error"]


def test_select_device_skips_missing_and_incompatible_paths(monkeypatch) -> None:
    monkeypatch.setattr(hid_protocol, "_query_feature_report", lambda _path: [0] * 5)

    assert hid_protocol.select_sprime_device([{}, {"path": b"short"}]) is None


def test_read_battery_classifies_generic_transport_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        hid_protocol,
        "_query_feature_report",
        lambda _path: (_ for _ in ()).throw(RuntimeError("transport failed")),
    )

    assert hid_protocol.read_battery(b"device") == {
        "status": "read_failed",
        "error": "transport failed",
    }


def test_get_battery_info_handles_each_selection_outcome(monkeypatch) -> None:
    monkeypatch.setattr(hid_protocol, "scan_devices", lambda: [])
    assert hid_protocol.get_battery_info() == {"status": "device_not_found"}

    monkeypatch.setattr(hid_protocol, "scan_devices", lambda: [{"path": b"one"}])
    monkeypatch.setattr(hid_protocol, "select_sprime_device", lambda _devices: None)
    assert hid_protocol.get_battery_info()["status"] == "protocol_unknown"

    monkeypatch.setattr(hid_protocol, "select_sprime_device", lambda _devices: {"path": None})
    assert "no HID path" in hid_protocol.get_battery_info()["error"]

    monkeypatch.setattr(hid_protocol, "select_sprime_device", lambda _devices: {"path": b"one"})
    monkeypatch.setattr(
        hid_protocol,
        "read_battery",
        lambda path: {"status": "connected", "path": path},
    )
    assert hid_protocol.get_battery_info() == {"status": "connected", "path": b"one"}
