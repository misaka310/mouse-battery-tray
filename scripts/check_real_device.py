from __future__ import annotations

import sys

from sprime_pm1_battery_tray.device_manager import DeviceManager


def main() -> int:
    manager = DeviceManager()
    try:
        result = manager.get_battery_info("auto")
    finally:
        manager.close()

    print(f"Battery info: {result}")
    status = str(result.get("status", "unknown"))
    battery = result.get("battery")
    if status == "connected" and isinstance(battery, int):
        print(
            f"Device verified: {result.get('device', 'Mouse')} "
            f"battery={battery}% charging={bool(result.get('charging', False))}"
        )
        return 0
    print(f"Device check failed with status: {status}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
