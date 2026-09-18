from __future__ import annotations

from typing import Any

from . import attack_shark
from . import hid_protocol


def get_battery_info() -> dict[str, Any]:
    """Read the first supported connected mouse using deterministic priority."""
    attack_result = attack_shark.get_battery_info()
    if attack_result.get("status") != "device_not_found":
        return attack_result

    sprime_result = hid_protocol.get_battery_info()
    if sprime_result.get("status") in {"connected", "disconnected"}:
        result = dict(sprime_result)
        result.setdefault("device", "SPRIME PM1")
        return result
    if sprime_result.get("status") != "device_not_found":
        result = dict(sprime_result)
        result.setdefault("device", "SPRIME PM1")
        return result

    return {"status": "device_not_found", "device": "Mouse"}
