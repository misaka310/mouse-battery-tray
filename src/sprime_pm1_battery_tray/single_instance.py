from __future__ import annotations

import ctypes
import os
import time

_MUTEX_NAME = "Local\\Mouse_Battery_Tray_SingleInstance"
_ERROR_ALREADY_EXISTS = 183
_mutex_handle: int | None = None


def acquire_single_instance() -> bool:
    """Keep one application instance per logged-in Windows session."""
    global _mutex_handle

    if os.name != "nt":
        return True

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    create_mutex.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_bool

    for attempt in range(2):
        ctypes.set_last_error(0)
        handle = create_mutex(None, False, _MUTEX_NAME)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())

        if ctypes.get_last_error() != _ERROR_ALREADY_EXISTS:
            _mutex_handle = int(handle)
            return True

        close_handle(ctypes.c_void_p(handle))
        if attempt == 0:
            time.sleep(0.5)

    return False
