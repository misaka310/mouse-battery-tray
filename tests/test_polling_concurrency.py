from __future__ import annotations

import threading

import pytest

from sprime_pm1_battery_tray.app import BatteryTrayApp


class StubManager:
    def __init__(self, read):
        self.read = read

    def get_battery_info(self, _preferred):
        return self.read()

    def close(self):
        pass


def make_app_with_lock(read=lambda: {"status": "device_not_found"}) -> BatteryTrayApp:
    instance = BatteryTrayApp.__new__(BatteryTrayApp)
    instance.poll_lock = threading.Lock()
    instance.config = {"preferred_device": "auto"}
    instance.device_manager = StubManager(read)
    return instance


def test_poll_once_skips_when_another_read_holds_lock():
    calls = []
    instance = make_app_with_lock(lambda: calls.append("read"))
    assert instance.poll_lock.acquire(blocking=False)

    try:
        assert instance.poll_once() is None
        assert calls == []
    finally:
        instance.poll_lock.release()


def test_poll_once_releases_lock_after_reader_exception():
    def fail_read():
        raise RuntimeError("HID read failed")

    instance = make_app_with_lock(fail_read)

    with pytest.raises(RuntimeError, match="HID read failed"):
        instance.poll_once()

    assert instance.poll_lock.acquire(blocking=False)
    instance.poll_lock.release()


def test_manual_and_periodic_reads_are_serialized():
    entered = threading.Event()
    release = threading.Event()
    results = []

    def slow_read():
        entered.set()
        release.wait(timeout=2)
        return {
            "status": "connected",
            "device": "ATTACK SHARK X1",
            "device_key": "attack_shark_x1",
            "battery": 80,
            "charging": False,
            "full": False,
        }

    instance = make_app_with_lock(slow_read)
    worker = threading.Thread(target=lambda: results.append(instance.poll_once()))
    worker.start()
    assert entered.wait(timeout=1)

    assert instance.poll_once() is None
    release.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert results[0]["battery"] == 80
