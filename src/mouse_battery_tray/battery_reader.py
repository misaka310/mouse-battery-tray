from __future__ import annotations

from typing import Any

from . import attack_shark


def get_battery_info() -> dict[str, Any]:
    """Read battery state from the active ATTACK SHARK adapter."""
    result = attack_shark.get_battery_info()
    if result.get("status") != "device_not_found":
        return result
    return {"status": "device_not_found", "device": "Mouse"}
