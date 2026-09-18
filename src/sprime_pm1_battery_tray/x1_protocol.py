from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import hid

# ATTACK SHARK X1 hardware observed in 2.4 GHz and wired modes.
VID = 0x1D57
WIRELESS_PID = 0xFA60
WIRED_PID = 0x2111

DEVICE_KEY = "attack_shark_x1"
WIRELESS_NAME = "ATTACK SHARK X1 / X11 family"
WIRED_NAME = "ATTACK SHARK X1 (wired)"

# The 0xFA60 receiver is shared by multiple Beken-based ATTACK SHARK models.
# Battery packets follow the public mouse-battery-tray implementation:
# [0x03, device_id, 0x40, subtype, battery, ...].
BATTERY_REPORT_ID = 0x03
BATTERY_MARKER = 0x40
CHARGING_SUBTYPES = {0x02, 0x03, 0x80}


def scan_devices() -> list[dict[str, Any]]:
    """Enumerate ATTACK SHARK/Beken endpoints for the X1 receiver and wired mouse."""
    return [
        device
        for device in hid.enumerate(VID)
        if int(device.get("product_id", -1)) in {WIRELESS_PID, WIRED_PID}
    ]


def _endpoint_rank(device: dict[str, Any]) -> tuple[int, int]:
    """Lower rank is better; mirror the proven Beken endpoint preference."""
    interface_number = int(device.get("interface_number", -1))
    usage_page = int(device.get("usage_page", 0))

    if interface_number == 2 and usage_page == 10:
        return (0, interface_number)
    if usage_page == 10 or usage_page >= 0xFF00 or interface_number == 2:
        return (1, interface_number)
    if interface_number == 1:
        return (2, interface_number)
    return (3, interface_number)


def select_wireless_endpoint(devices: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        device
        for device in devices
        if int(device.get("vendor_id", VID)) == VID
        and int(device.get("product_id", -1)) == WIRELESS_PID
        and device.get("path")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=_endpoint_rank)[0]


def parse_battery_packet(data: Sequence[int] | None) -> dict[str, Any] | None:
    """Parse one Beken input report. Non-battery reports return None."""
    if not data or len(data) < 5:
        return None

    try:
        values = [int(value) for value in data]
    except (TypeError, ValueError):
        return None

    if values[0] != BATTERY_REPORT_ID:
        return None

    if values[2] == BATTERY_MARKER:
        raw_battery = values[4]
    else:
        candidate = values[4]
        raw_battery = candidate if 0 < candidate <= 100 else values[2]

    if not 0 <= raw_battery <= 100:
        return None

    charging = values[3] in CHARGING_SUBTYPES
    return {
        "status": "connected",
        "battery": raw_battery,
        "charging": charging,
        "full": raw_battery >= 100,
        "device_key": DEVICE_KEY,
        "device": WIRELESS_NAME,
        "recommended_refresh_sec": 2,
    }


class X1BatteryReader:
    """Keep the receiver handle open so passive battery heartbeats are not missed."""

    def __init__(self) -> None:
        self._handle = None
        self._path = None
        self._last_result: dict[str, Any] | None = None
        self._last_packet_at = 0.0

    def close(self) -> None:
        handle = self._handle
        self._handle = None
        self._path = None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass

    def _open(self, path: Any) -> None:
        if self._handle is not None and self._path == path:
            return

        self.close()
        handle = hid.device()
        try:
            handle.open_path(path.encode("utf-8") if isinstance(path, str) else path)
            handle.set_nonblocking(True)
        except Exception:
            try:
                handle.close()
            except Exception:
                pass
            raise

        self._handle = handle
        self._path = path

    def read(self, timeout_sec: float = 1.0) -> dict[str, Any]:
        try:
            devices = scan_devices()
        except Exception as exc:
            self.close()
            return {
                "status": "enumeration_failed",
                "error": str(exc) or exc.__class__.__name__,
                "device_key": DEVICE_KEY,
                "device": WIRELESS_NAME,
                "recommended_refresh_sec": 5,
            }

        wireless = select_wireless_endpoint(devices)
        if wireless is None:
            self.close()
            wired_present = any(
                int(device.get("product_id", -1)) == WIRED_PID for device in devices
            )
            if wired_present:
                return {
                    "status": "connected",
                    "battery": None,
                    "charging": True,
                    "full": False,
                    "device_key": DEVICE_KEY,
                    "device": WIRED_NAME,
                    "recommended_refresh_sec": 5,
                }
            self._last_result = None
            self._last_packet_at = 0.0
            return {
                "status": "device_not_found",
                "device_key": DEVICE_KEY,
                "device": WIRELESS_NAME,
                "recommended_refresh_sec": 5,
            }

        path = wireless.get("path")
        try:
            self._open(path)
        except Exception as exc:
            self.close()
            return {
                "status": "permission_or_access_error",
                "error": str(exc) or exc.__class__.__name__,
                "device_key": DEVICE_KEY,
                "device": WIRELESS_NAME,
                "recommended_refresh_sec": 5,
            }

        deadline = time.monotonic() + max(0.0, timeout_sec)
        while True:
            try:
                data = self._handle.read(64)
            except Exception as exc:
                self.close()
                return {
                    "status": "read_failed",
                    "error": str(exc) or exc.__class__.__name__,
                    "device_key": DEVICE_KEY,
                    "device": WIRELESS_NAME,
                    "recommended_refresh_sec": 5,
                }

            parsed = parse_battery_packet(data)
            if parsed is not None:
                self._last_result = parsed
                self._last_packet_at = time.monotonic()
                return dict(parsed)

            if time.monotonic() >= deadline:
                break
            time.sleep(0.02)

        # A sleeping mouse may temporarily stop sending heartbeats. Keep a recent,
        # verified value instead of flickering the tray icon between a number and --.
        if self._last_result is not None and time.monotonic() - self._last_packet_at <= 60:
            return dict(self._last_result)

        return {
            "status": "disconnected",
            "battery": None,
            "charging": False,
            "full": False,
            "device_key": DEVICE_KEY,
            "device": WIRELESS_NAME,
            "recommended_refresh_sec": 2,
        }
