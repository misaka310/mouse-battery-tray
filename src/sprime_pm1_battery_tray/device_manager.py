from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .hid_protocol import get_battery_info as read_sprime_pm1
from .x1_protocol import X1BatteryReader

AUTO = "auto"
X1 = "attack_shark_x1"
PM1 = "sprime_pm1"
VALID_PREFERENCES = {AUTO, X1, PM1}


class DeviceManager:
    """Select one supported mouse while keeping device-specific HID code isolated."""

    def __init__(
        self,
        x1_reader: X1BatteryReader | None = None,
        pm1_reader: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self.x1_reader = x1_reader or X1BatteryReader()
        self.pm1_reader = pm1_reader or read_sprime_pm1

    @staticmethod
    def _with_pm1_metadata(result: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(result)
        normalized.setdefault("device_key", PM1)
        normalized.setdefault("device", "SPRIME PM1")
        return normalized

    def _read_x1(self) -> dict[str, Any]:
        return self.x1_reader.read()

    def _read_pm1(self) -> dict[str, Any]:
        return self._with_pm1_metadata(self.pm1_reader())

    @staticmethod
    def _has_battery(result: dict[str, Any]) -> bool:
        return (
            result.get("status") == "connected"
            and isinstance(result.get("battery"), int)
            and 0 <= int(result["battery"]) <= 100
        )

    @staticmethod
    def _is_connected(result: dict[str, Any]) -> bool:
        return result.get("status") == "connected"

    def get_battery_info(self, preferred: str = AUTO) -> dict[str, Any]:
        if preferred not in VALID_PREFERENCES:
            preferred = AUTO

        readers = {
            X1: self._read_x1,
            PM1: self._read_pm1,
        }
        order = [X1, PM1]
        if preferred == PM1:
            order = [PM1, X1]
        elif preferred == X1:
            order = [X1, PM1]

        results: list[dict[str, Any]] = []
        for key in order:
            try:
                result = readers[key]()
            except Exception as exc:
                result = {
                    "status": "read_failed",
                    "error": str(exc) or exc.__class__.__name__,
                    "device_key": key,
                    "device": "ATTACK SHARK X1 / X11 family" if key == X1 else "SPRIME PM1",
                }
            results.append(result)
            if self._has_battery(result):
                return result

        for result in results:
            if self._is_connected(result):
                return result

        for result in results:
            if result.get("status") not in {"device_not_found", "disconnected"}:
                return result

        # Preserve a detected receiver/sleep state over a generic no-device state.
        for result in results:
            if result.get("status") == "disconnected":
                return result

        return {
            "status": "device_not_found",
            "device": "Mouse",
            "device_key": AUTO,
            "recommended_refresh_sec": 5,
        }

    def close(self) -> None:
        self.x1_reader.close()
