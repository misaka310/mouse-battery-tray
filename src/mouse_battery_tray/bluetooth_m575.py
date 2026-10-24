"""Read Windows-reported Bluetooth battery for Logitech ERGO M575.

Uses Config Manager's read-only PnP properties. No PowerShell processes, HID
input injection, driver replacement, or Bluetooth pairing changes are needed.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import uuid
from ctypes import wintypes
from typing import Any

_BATTERY_GUID = "104EA319-6EE2-4701-BD47-8DDBF425BBE5"
_FRIENDLY_GUID = "A45C254E-DF1C-4EFD-8020-67D146A850E0"
_CM_GETIDLIST_FILTER_PRESENT = 0x100
_DEVPROP_TYPE_BYTE = 3


class _DEVPROPKEY(ctypes.Structure):
    _fields_ = [("fmtid", ctypes.c_ubyte * 16), ("pid", wintypes.DWORD)]


def _make_key(guid: str, pid: int) -> _DEVPROPKEY:
    key = _DEVPROPKEY()
    key.fmtid[:] = uuid.UUID(guid).bytes_le
    key.pid = pid
    return key


def _get_api() -> Any:
    api = ctypes.WinDLL("CfgMgr32.dll")
    api.CM_Get_Device_ID_List_SizeW.argtypes = [
        ctypes.POINTER(wintypes.ULONG), wintypes.LPCWSTR, wintypes.ULONG,
    ]
    api.CM_Get_Device_ID_ListW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.ULONG, wintypes.ULONG,
    ]
    api.CM_Locate_DevNodeW.argtypes = [
        ctypes.POINTER(wintypes.ULONG), wintypes.LPWSTR, wintypes.ULONG,
    ]
    api.CM_Get_DevNode_PropertyW.argtypes = [
        wintypes.ULONG, ctypes.POINTER(_DEVPROPKEY),
        ctypes.POINTER(wintypes.ULONG), ctypes.c_void_p,
        ctypes.POINTER(wintypes.ULONG), wintypes.ULONG,
    ]
    return api


def _present_device_ids(api: Any) -> list[str]:
    length = wintypes.ULONG()
    if api.CM_Get_Device_ID_List_SizeW(
        ctypes.byref(length), None, _CM_GETIDLIST_FILTER_PRESENT,
    ) != 0 or length.value == 0:
        return []
    buffer = ctypes.create_unicode_buffer(length.value + 1)
    if api.CM_Get_Device_ID_ListW(
        None, buffer, len(buffer), _CM_GETIDLIST_FILTER_PRESENT,
    ) != 0:
        return []
    return [s for s in buffer[:].split("\0") if s.startswith(("BTH", "SWD"))]


def _read_property(api: Any, devnode: int, key: _DEVPROPKEY) -> tuple[int, bytes] | None:
    data = (ctypes.c_ubyte * 256)()
    length = wintypes.ULONG(len(data))
    value_type = wintypes.ULONG()
    result = api.CM_Get_DevNode_PropertyW(
        devnode, ctypes.byref(key), ctypes.byref(value_type),
        data, ctypes.byref(length), 0,
    )
    if result != 0 or length.value > len(data):
        return None
    return value_type.value, bytes(data[:length.value])


def get_battery_infos() -> list[dict[str, Any]]:
    """Return just ERGO M575 mice with a valid Windows Bluetooth battery value."""
    if os.name != "nt":
        return []

    try:
        api = _get_api()
        result = []
        battery_key = _make_key(_BATTERY_GUID, 2)
        name_key = _make_key(_FRIENDLY_GUID, 14)
        for device_id in _present_device_ids(api):
            devnode = wintypes.ULONG()
            if api.CM_Locate_DevNodeW(
                ctypes.byref(devnode), ctypes.c_wchar_p(device_id), 0,
            ) != 0:
                continue
            battery = _read_property(api, devnode.value, battery_key)
            if not battery or battery[0] != _DEVPROP_TYPE_BYTE or len(battery[1]) != 1:
                continue
            level = battery[1][0]
            if level > 100:
                continue
            name_value = _read_property(api, devnode.value, name_key)
            if not name_value:
                continue
            name = name_value[1].decode("utf-16-le", errors="replace").rstrip("\0")
            if "M575" not in name.upper():
                continue
            result.append({
                "status": "connected",
                "device": "Logitech ERGO M575",
                "battery": level,
                "charging": False,
                "full": level >= 100,
                "receiver_id": "bt-" + hashlib.sha256(device_id.encode("utf-8")).hexdigest()[:12],
                "source": "windows_bluetooth",
            })
        return result
    except (OSError, AttributeError, ValueError):
        return []
