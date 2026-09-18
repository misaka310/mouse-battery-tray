from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mouse_battery_tray.battery_reader import get_battery_info  # noqa: E402


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
