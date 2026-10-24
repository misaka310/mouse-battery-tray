from __future__ import annotations

from typing import Any

from . import attack_shark


def get_battery_info() -> dict[str, Any]:
    """Read battery state from the active ATTACK SHARK adapter."""
    result = attack_shark.get_battery_info()
    if result.get("status") != "device_not_found":
        return result
    return {"status": "device_not_found", "device": "Mouse"}

def get_monitor_info() -> dict[str, Any]:
    """Aggregate independent mice, with the lowest connected battery on the tray."""
    from . import bluetooth_m575, ry24g

    devices = (
        attack_shark.get_battery_infos()
        + ry24g.get_battery_infos()
        + bluetooth_m575.get_battery_infos()
    )
    devices.sort(key=lambda d: (str(d.get("device", "")), str(d.get("receiver_id", ""))))
    connected = [
        device for device in devices
        if device.get("status") == "connected"
        and type(device.get("battery")) is int
    ]

    if connected:
        lowest = min(connected, key=lambda device: int(device["battery"]))
        return {
            "status": "connected",
            "device": lowest["device"] if len(devices) == 1 else f"{len(devices)} mice",
            "battery": lowest["battery"],
            "charging": bool(lowest.get("charging", False)),
            "full": bool(lowest.get("full", False)),
            "devices": devices,
        }

    if devices:
        problem = next(
            (device for device in devices if device.get("status") not in {"disconnected", "device_not_found"}),
            devices[0],
        )
        return {
            "status": problem.get("status", "disconnected"),
            "device": problem.get("device", "Mouse"),
            "battery": "--",
            "charging": False,
            "full": False,
            "error": problem.get("error", ""),
            "devices": devices,
        }
    return {
        "status": "device_not_found",
        "device": "Mouse",
        "battery": "--",
        "charging": False,
        "full": False,
        "devices": [],
    }
