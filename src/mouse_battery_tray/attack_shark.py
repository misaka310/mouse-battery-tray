from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import hid

VID = 0x1D57
PID = 0xFA60

# Confirmed on the user's ATTACK SHARK X1 on 2026-09-18.
BATTERY_INTERFACE_NUMBER = 2
BATTERY_USAGE_PAGE = 0x0A
BATTERY_REPORT_PREFIX = 0x03
BATTERY_REPORT_TYPE = 0x40
DEFAULT_READ_TIMEOUT_SEC = 5.0

# Device IDs observed in the Beken-family packet format. Existing mappings are
# adapted from incconutwo/mouse-battery-tray (MIT); 0xB1 was verified on X1.
DEVICE_NAMES = {
    0xB1: "ATTACK SHARK X1",
    0x55: "ATTACK SHARK X11",
    0x10: "ATTACK SHARK R1",
    0x85: "ATTACK SHARK X6",
    0x4D: "ATTACK SHARK X3",
    0xBE: "ATTACK SHARK X11 Pro",
    0x07: "ATTACK SHARK X11 SE",
}


def scan_devices() -> list[dict[str, Any]]:
    """Enumerate the ATTACK SHARK 2.4 GHz receiver endpoints."""
    return list(hid.enumerate(VID, PID))


def select_battery_endpoint(devices: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    """Prefer the verified interface 2 / usage-page 0x0A battery endpoint."""
    for device in devices:
        if (
            int(device.get("interface_number", -1)) == BATTERY_INTERFACE_NUMBER
            and int(device.get("usage_page", 0)) == BATTERY_USAGE_PAGE
        ):
            return device

    # Keep a conservative fallback for compatible Beken-family receivers where
    # Windows reports the same interface but a vendor usage page.
    for device in devices:
        usage_page = int(device.get("usage_page", 0))
        if int(device.get("interface_number", -1)) == BATTERY_INTERFACE_NUMBER and usage_page >= 0xFF00:
            return device
    return None


def parse_battery_packet(packet: Sequence[int] | None) -> dict[str, Any] | None:
    """Parse one Beken-family packet into the common battery result shape."""
    if not packet or len(packet) < 5:
        return None

    try:
        report_id = int(packet[0])
        device_id = int(packet[1])
        report_type = int(packet[2])
        subtype = int(packet[3])
        raw_battery = int(packet[4])
    except (TypeError, ValueError, IndexError):
        return None

    if report_id != BATTERY_REPORT_PREFIX or report_type != BATTERY_REPORT_TYPE:
        return None

    # X6 is known to use a 1-10 scale. Other mapped devices, including the
    # verified X1, report a normal percentage.
    battery = raw_battery * 10 if device_id == 0x85 and 0 < raw_battery <= 10 else raw_battery
    if not 0 <= battery <= 100:
        return None

    charging = subtype in (0x02, 0x03, 0x80)
    return {
        "status": "connected",
        "device": DEVICE_NAMES.get(device_id, "ATTACK SHARK Mouse"),
        "battery": battery,
        "charging": charging,
        "full": battery >= 100,
        "device_id": device_id,
    }


def _classify_error(exc: Exception) -> dict[str, Any]:
    error_text = str(exc) or exc.__class__.__name__
    lowered = error_text.lower()
    status = (
        "permission_or_access_error"
        if "open" in lowered or "access" in lowered or "permission" in lowered
        else "read_failed"
    )
    return {"status": status, "device": "ATTACK SHARK Mouse", "error": error_text}


def read_battery(device_path: Any, timeout_sec: float = DEFAULT_READ_TIMEOUT_SEC) -> dict[str, Any]:
    """Wait briefly for the receiver's passive battery heartbeat."""
    if not device_path:
        return {
            "status": "protocol_unknown",
            "device": "ATTACK SHARK Mouse",
            "error": "Compatible ATTACK SHARK endpoint has no HID path",
        }

    handle = hid.device()
    try:
        handle.open_path(device_path)
        handle.set_nonblocking(True)
    except Exception as exc:
        try:
            handle.close()
        except Exception:
            pass
        return _classify_error(exc)

    deadline = time.monotonic() + max(0.0, float(timeout_sec))
    try:
        while time.monotonic() < deadline:
            try:
                packet = handle.read(64)
            except Exception as exc:
                return _classify_error(exc)

            result = parse_battery_packet(packet)
            if result is not None:
                return result
            time.sleep(0.02)
    finally:
        try:
            handle.close()
        except Exception:
            pass

    # A sleeping mouse can leave the receiver present without sending a battery
    # heartbeat. Treat that as unavailable, not as a transport error.
    return {
        "status": "disconnected",
        "device": "ATTACK SHARK X1",
        "battery": "--",
        "charging": False,
        "full": False,
    }


def get_battery_info(timeout_sec: float = DEFAULT_READ_TIMEOUT_SEC) -> dict[str, Any]:
    try:
        devices = scan_devices()
    except Exception as exc:
        return {"status": "enumeration_failed", "device": "ATTACK SHARK Mouse", "error": str(exc) or exc.__class__.__name__}

    if not devices:
        return {"status": "device_not_found"}

    endpoint = select_battery_endpoint(devices)
    if endpoint is None:
        return {
            "status": "protocol_unknown",
            "device": "ATTACK SHARK Mouse",
            "error": "Could not find compatible ATTACK SHARK battery endpoint",
        }

    return read_battery(endpoint.get("path"), timeout_sec=timeout_sec)
