from __future__ import annotations

import os
import sys
import tempfile

import atheris

with atheris.instrument_imports():
    from mouse_battery_tray.config import _read_config


def TestOneInput(data: bytes) -> None:
    fd, path = tempfile.mkstemp(prefix="mouse-battery-fuzz-", suffix=".json")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        try:
            config = _read_config(path)
            if not isinstance(config, dict):
                raise AssertionError("config parser returned a non-dict")
        except (OSError, UnicodeError, ValueError, TypeError):
            pass
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
