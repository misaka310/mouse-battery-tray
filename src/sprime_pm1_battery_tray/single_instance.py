from __future__ import annotations

import ctypes
import os
import time

_MUTEX_NAMES = (
    "Local\\Mouse_Battery_Tray_SingleInstance",
    "Local\\SPRIME_PM1_Battery_Tray_SingleInstance",
)
_ERROR_ALREADY_EXISTS = 183
_mutex_handles: list[int] = []


def acquire_single_instance() -> bool:
    """Keep one generic or legacy tray instance per logged-in Windows session."""
    global _mutex_handles

    if os.name != "nt":
        return True

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    create_mutex.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_bool

    acquired: list[int] = []
    for mutex_name in _MUTEX_NAMES:
        for attempt in range(2):
            ctypes.set_last_error(0)
            handle = create_mutex(None, False, mutex_name)
            if not handle:
                for owned in acquired:
                    close_handle(ctypes.c_void_p(owned))
                raise ctypes.WinError(ctypes.get_last_error())

            if ctypes.get_last_error() != _ERROR_ALREADY_EXISTS:
                acquired.append(int(handle))
                break

            close_handle(ctypes.c_void_p(handle))
            if attempt == 0:
                time.sleep(0.5)
                continue

            for owned in acquired:
                close_handle(ctypes.c_void_p(owned))
            return False

    _mutex_handles = acquired
    return True
