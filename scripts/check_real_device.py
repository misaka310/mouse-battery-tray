from __future__ import annotations

import sys

from sprime_pm1_battery_tray.battery_reader import get_battery_info


def main() -> int:
    result = get_battery_info()
    print(f"Battery info: {result}")
    status = str(result.get("status", "unknown"))
    if status in {"connected", "disconnected"}:
        print(f"Device found with status: {status}")
        return 0
    print(f"Device check failed with status: {status}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
