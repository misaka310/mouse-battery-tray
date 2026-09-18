from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import hid

# Vendor ID and Product ID for SPRIME PM1
VID = 0x1915
PID = 0xAC1C

FEATURE_REPORT_ID = 0x05
QUERY_COMMAND = 0x15
QUERY_FLAG = 0x01
REPORT_LENGTH = 32
MIN_RESPONSE_LENGTH = 14


class SprimeDeviceError(Exception):
    """Raised when the HID transport cannot complete the PM1 query contract."""


def scan_devices() -> list[dict[str, Any]]:
    """Enumerate HID endpoints matching the known SPRIME PM1 VID/PID pair."""
    return list(hid.enumerate(VID, PID))


def _decode_path(device: dict[str, Any]) -> str:
    path = device.get("path", b"")
    if isinstance(path, bytes):
        return path.decode("ascii", errors="ignore")
    return str(path or "")


def _query_feature_report(device_path: Any) -> Sequence[int]:
    """Send the PM1 battery query and always release the native HID handle."""
    if not device_path:
        raise SprimeDeviceError("HID device path is required")

    handle = hid.device()
    try:
        handle.open_path(device_path)
        handle.set_nonblocking(0)

        buffer = bytearray(REPORT_LENGTH)
        buffer[0] = FEATURE_REPORT_ID
        buffer[1] = QUERY_COMMAND
        buffer[4] = QUERY_FLAG

        sent = handle.send_feature_report(buffer)
        if not isinstance(sent, int) or sent <= 0:
            raise SprimeDeviceError("HID feature report command was not accepted")

        time.sleep(0.05)
        response = handle.get_feature_report(FEATURE_REPORT_ID, REPORT_LENGTH)
        if not response:
            raise SprimeDeviceError("HID feature report returned no response")
        return response
    finally:
        try:
            handle.close()
        except Exception:
            # Closing is best-effort because the original transport error is more useful.
            pass


def parse_battery_report(report: Sequence[int] | None) -> dict[str, Any]:
    """Validate and convert a raw feature report into a stable application result."""
    if not report or len(report) < MIN_RESPONSE_LENGTH:
        return {"status": "read_failed", "error": "Invalid response length"}

    try:
        battery = int(report[9])
        charging_raw = int(report[10])
        full_raw = int(report[11])
        online_raw = int(report[12])
    except (IndexError, TypeError, ValueError) as exc:
        return {"status": "invalid_report", "error": f"Invalid report values: {exc}"}

    if not 0 <= battery <= 100:
        return {"status": "invalid_report", "error": f"Battery value out of range: {battery}"}

    invalid_flags = {
        "charging": charging_raw,
        "full": full_raw,
        "online": online_raw,
    }
    invalid_flags = {
        name: value for name, value in invalid_flags.items() if value not in (0, 1)
    }
    if invalid_flags:
        detail = ", ".join(f"{name}={value}" for name, value in invalid_flags.items())
        return {"status": "invalid_report", "error": f"Invalid boolean flag values: {detail}"}

    charging = bool(charging_raw)
    full = bool(full_raw)
    online = bool(online_raw)

    if not online:
        return {
            "status": "disconnected",
            "battery": battery,
            "charging": charging,
            "full": full,
        }
    return {
        "status": "connected",
        "battery": battery,
        "charging": charging,
        "full": full,
    }


def select_sprime_device(devices: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    """Prefer the known Col04 endpoint, then probe remaining valid HID paths."""
    for device in devices:
        if "col04" in _decode_path(device).lower():
            return device

    for device in devices:
        device_path = device.get("path")
        if not device_path:
            continue
        try:
            report = _query_feature_report(device_path)
            if report and len(report) >= MIN_RESPONSE_LENGTH:
                return device
        except Exception:
            # Composite HID devices expose endpoints that legitimately reject this query.
            continue
    return None


def read_battery(device_path: Any) -> dict[str, Any]:
    """Read one endpoint and classify transport failures for the tray UI."""
    try:
        report = _query_feature_report(device_path)
    except Exception as exc:
        error_text = str(exc)
        lowered = error_text.lower()
        status = (
            "permission_or_access_error"
            if "open" in lowered or "access" in lowered or "permission" in lowered
            else "read_failed"
        )
        return {"status": status, "error": error_text or exc.__class__.__name__}

    return parse_battery_report(report)


def get_battery_info() -> dict[str, Any]:
    """Execute enumeration, endpoint selection, and reading as one safe polling operation."""
    try:
        devices = scan_devices()
    except Exception as exc:
        return {"status": "enumeration_failed", "error": str(exc) or exc.__class__.__name__}

    if not devices:
        return {"status": "device_not_found"}

    device = select_sprime_device(devices)
    if not device:
        return {
            "status": "protocol_unknown",
            "error": "Could not find compatible SPRIME endpoint",
        }

    device_path = device.get("path")
    if not device_path:
        return {
            "status": "protocol_unknown",
            "error": "Compatible SPRIME endpoint has no HID path",
        }
    return read_battery(device_path)
