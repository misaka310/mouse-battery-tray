from __future__ import annotations

import threading

import pytest

from mouse_battery_tray import app as app_module
from mouse_battery_tray.app import BatteryTrayApp


def make_app_with_lock() -> BatteryTrayApp:
    instance = BatteryTrayApp.__new__(BatteryTrayApp)
    instance.poll_lock = threading.Lock()
    return instance


def test_poll_once_skips_when_another_read_holds_lock(monkeypatch):
    instance = make_app_with_lock()
    assert instance.poll_lock.acquire(blocking=False)
    calls = []
    monkeypatch.setattr(app_module, "get_battery_info", lambda: calls.append("read"))

    try:
        assert instance.poll_once() is None
        assert calls == []
    finally:
        instance.poll_lock.release()


def test_poll_once_releases_lock_after_reader_exception(monkeypatch):
    instance = make_app_with_lock()

    def fail_read():
        raise RuntimeError("HID read failed")

    monkeypatch.setattr(app_module, "get_battery_info", fail_read)

    with pytest.raises(RuntimeError, match="HID read failed"):
        instance.poll_once()

    assert instance.poll_lock.acquire(blocking=False)
    instance.poll_lock.release()


def test_manual_and_periodic_reads_are_serialized(monkeypatch):
    instance = make_app_with_lock()
    entered = threading.Event()
    release = threading.Event()
    results = []

    def slow_read():
        entered.set()
        release.wait(timeout=2)
        return {"status": "connected", "battery": 80, "charging": False, "full": False}

    monkeypatch.setattr(app_module, "get_battery_info", slow_read)
    worker = threading.Thread(target=lambda: results.append(instance.poll_once()))
    worker.start()
    assert entered.wait(timeout=1)

    assert instance.poll_once() is None
    release.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert results[0]["battery"] == 80
