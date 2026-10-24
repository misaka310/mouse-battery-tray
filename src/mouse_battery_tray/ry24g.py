"""Read battery status from the 3151:5031 Ry24G receiver used by this X1.

Only the documented 0xF7 status query is sent; configuration, device
selection, input emulation and firmware commands are deliberately excluded.

Observed on DESK2 (2026-10-25): status payload 00 00 61 01 01 01
(repeated three times). The receiver reported 97%, but its mouse-online
flag indicated offline. Never promote an offline cached level to a current
battery reading.
"""
from __future__ import annotations

import hashlib
import time
from collections.abc import Sequence
from typing import Any

import hid

VID = 0x3151
PID = 0x5031
INTERFACE_NUMBER = 2
USAGE_PAGE = 0xFFFF
USAGE = 0x0002
FEATURE_REPORT_ID = 0
FEATURE_PAYLOAD_SIZE = 64
FEATURE_WIRE_SIZE = FEATURE_PAYLOAD_SIZE + 1
STATUS_COMMAND = 0xF7
DEVICE_LABEL = "ATTACK SHARK X1 (Ry24G)"


def scan_devices() -> list[dict[str, Any]]:
    return [
        device for device in hid.enumerate(VID, PID)
        if int(device.get("interface_number", -1)) == INTERFACE_NUMBER
        and int(device.get("usage_page", -1)) == USAGE_PAGE
        and int(device.get("usage", -1)) == USAGE
    ]


def parse_status(report: Sequence[int]) -> dict[str, Any] | None:
    """Decode a HIDAPI report, including the leading report-ID 0.

    Status offsets follow the receiver's documented 0xF7 reply:
      payload[0] = canRead, payload[1] = keyboard battery,
      payload[2] = mouse battery, payload[3] = keyboard offline flag,
      payload[4] = mouse offline flag, payload[5] = canSend.
    """
    if len(report) != FEATURE_WIRE_SIZE or int(report[0]) != FEATURE_REPORT_ID:
        return None

    payload = report[1:]
    if any(payload[index] not in (0, 1) for index in (0, 3, 4, 5)):
        return None

    level = int(payload[2])
    if not 0 <= level <= 100:
        return None

    connected = payload[4] == 0
    result: dict[str, Any] = {
        "device": DEVICE_LABEL,
        "status": "connected" if connected else "disconnected",
        "battery": level if connected else "--",
        "charging": False,
        "full": connected and level >= 100,
        "source": "ry24g_feature_status",
    }
    if not connected:
        result["last_reported_battery"] = level
    return result


def _identity(path: Any) -> str:
    if isinstance(path, bytes):
        path_bytes = path
    else:
        path_bytes = str(path).encode("utf-8", errors="replace")
    return "ry24g-" + hashlib.sha256(path_bytes).hexdigest()[:12]


def read_battery(path: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "device": DEVICE_LABEL,
        "receiver_id": _identity(path),
        "status": "disconnected",
        "battery": "--",
        "charging": False,
        "full": False,
    }
    if not path:
        return {**result, "status": "protocol_unknown", "error": "Missing receiver path"}

    handle = hid.device()
    try:
        handle.open_path(path)
        # Feature report ID 0, with exactly 64 payload bytes as in the
        # official web client's status query.
        sent = handle.send_feature_report(
            bytes([FEATURE_REPORT_ID, STATUS_COMMAND] + [0] * (FEATURE_PAYLOAD_SIZE - 1))
        )
        if sent != FEATURE_WIRE_SIZE:
            return {**result, "status": "read_failed", "error": "Status query was not accepted"}
        time.sleep(0.04)
        report = handle.get_feature_report(FEATURE_REPORT_ID, FEATURE_WIRE_SIZE)
        parsed = parse_status(report)
        if parsed is None:
            return {**result, "status": "protocol_unknown", "error": "Invalid Ry24G status report"}
        return {**result, **parsed}
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        kind = "permission_or_access_error" if any(
            token in message.lower() for token in ("open", "permission", "access")
        ) else "read_failed"
        return {**result, "status": kind, "error": message}
    finally:
        try:
            handle.close()
        except Exception:
            pass


def get_battery_infos() -> list[dict[str, Any]]:
    try:
        devices = scan_devices()
    except Exception as exc:
        return [{
            "device": DEVICE_LABEL,
            "receiver_id": "ry24g-enumeration",
            "status": "enumeration_failed",
            "battery": "--",
            "charging": False,
            "full": False,
            "error": str(exc) or exc.__class__.__name__,
        }]

    # Only one interface 2 / FFFF:0002 collection per physical receiver is
    # expected. Paths are unique, so multiple identical dongles remain distinct.
    unique = {
        _identity(device.get("path")): device.get("path")
        for device in devices if device.get("path")
    }
    return [read_battery(unique[key]) for key in sorted(unique)]
