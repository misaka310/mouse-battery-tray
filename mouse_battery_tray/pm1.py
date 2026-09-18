from __future__ import annotations

import time
from typing import Optional, Tuple, Any

import hid

VID = 0x1915
PID = 0xAC1C
FEATURE_REPORT_ID = 0x05
QUERY_COMMAND = 0x15
QUERY_FLAG = 0x01
REPORT_LENGTH = 32
MIN_RESPONSE_LENGTH = 14


def _query(path: Any):
    if not path:
        return None
    dev = hid.device()
    try:
        dev.open_path(path)
        dev.set_nonblocking(0)
        report = bytearray(REPORT_LENGTH)
        report[0] = FEATURE_REPORT_ID
        report[1] = QUERY_COMMAND
        report[4] = QUERY_FLAG
        sent = dev.send_feature_report(report)
        if not isinstance(sent, int) or sent <= 0:
            return None
        time.sleep(0.05)
        response = dev.get_feature_report(FEATURE_REPORT_ID, REPORT_LENGTH)
        return response or None
    except (OSError, ValueError):
        return None
    finally:
        try:
            dev.close()
        except Exception:
            pass


def _decode_path(device: dict) -> str:
    path = device.get("path", b"")
    if isinstance(path, bytes):
        return path.decode("ascii", errors="ignore")
    return str(path or "")


def find_pm1() -> Optional[Any]:
    """Find the known SPRIME PM1 endpoint, preferring Col04."""
    try:
        devices = list(hid.enumerate(VID, PID))
    except Exception:
        return None

    for device in devices:
        if "col04" in _decode_path(device).lower() and device.get("path"):
            return device["path"]

    for device in devices:
        path = device.get("path")
        if path and _query(path):
            return path
    return None


def read_pm1_battery(path: Any) -> Tuple[Optional[int], Optional[bool]]:
    """Return (battery_percent, charging) for SPRIME PM1."""
    response = _query(path)
    if not response or len(response) < MIN_RESPONSE_LENGTH:
        return None, None
    try:
        battery = int(response[9])
        charging = int(response[10])
        online = int(response[12])
    except (IndexError, TypeError, ValueError):
        return None, None
    if not 0 <= battery <= 100 or charging not in (0, 1) or online not in (0, 1):
        return None, None
    if not online:
        return None, None
    return battery, bool(charging)
