from types import SimpleNamespace

import pm1


def test_pm1_parse_and_read(monkeypatch):
    report = [0] * 32
    report[9] = 88
    report[10] = 0
    report[12] = 1
    monkeypatch.setattr(pm1, "_query", lambda path: report)
    assert pm1.read_pm1_battery(b"pm1") == (88, False)


def test_pm1_prefers_col04(monkeypatch):
    devices = [
        {"path": b"abc-col02"},
        {"path": b"abc-Col04"},
    ]
    monkeypatch.setattr(pm1.hid, "enumerate", lambda vid, pid: devices)
    assert pm1.find_pm1() == b"abc-Col04"


def test_x1_mapping_and_receiver_are_present():
    import devices
    assert (0x1D57, 0xFA60) in devices.SUPPORTED_DEVICES
    assert devices.SUPPORTED_DEVICES[(0x1D57, 0xFA60)][0] == "ATTACK SHARK X1"
