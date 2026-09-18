from sprime_pm1_battery_tray.device_manager import DeviceManager


class StubX1:
    def __init__(self, result):
        self.result = result
        self.closed = False

    def read(self):
        return dict(self.result)

    def close(self):
        self.closed = True


def connected(device, battery):
    return {
        "status": "connected",
        "device": device,
        "battery": battery,
        "charging": False,
        "full": battery == 100,
    }


def test_auto_prefers_x1_when_both_have_valid_battery():
    manager = DeviceManager(
        x1_reader=StubX1(connected("ATTACK SHARK X1", 70)),
        pm1_reader=lambda: connected("SPRIME PM1", 80),
    )
    result = manager.get_battery_info("auto")
    assert result["battery"] == 70
    assert result["device_key"] == "attack_shark_x1"


def test_pm1_preference_changes_priority():
    manager = DeviceManager(
        x1_reader=StubX1(connected("ATTACK SHARK X1", 70)),
        pm1_reader=lambda: connected("SPRIME PM1", 80),
    )
    result = manager.get_battery_info("sprime_pm1")
    assert result["battery"] == 80
    assert result["device_key"] == "sprime_pm1"


def test_preferred_device_falls_back_when_it_has_no_readable_battery():
    manager = DeviceManager(
        x1_reader=StubX1(
            {
                "status": "disconnected",
                "battery": None,
                "device": "ATTACK SHARK X1",
                "device_key": "attack_shark_x1",
            }
        ),
        pm1_reader=lambda: connected("SPRIME PM1", 45),
    )
    result = manager.get_battery_info("attack_shark_x1")
    assert result["battery"] == 45
    assert result["device_key"] == "sprime_pm1"


def test_all_missing_returns_generic_state():
    manager = DeviceManager(
        x1_reader=StubX1({"status": "device_not_found"}),
        pm1_reader=lambda: {"status": "device_not_found"},
    )
    result = manager.get_battery_info("auto")
    assert result == {
        "status": "device_not_found",
        "device": "Mouse",
        "device_key": "auto",
        "recommended_refresh_sec": 5,
    }


def test_close_releases_stateful_x1_reader():
    x1 = StubX1({"status": "device_not_found"})
    manager = DeviceManager(x1_reader=x1, pm1_reader=lambda: {"status": "device_not_found"})
    manager.close()
    assert x1.closed is True
