from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    import hid  # noqa: F401
except ImportError:
    # The packet parser itself does not touch HID I/O. Keep the fuzz target
    # independent from host USB libraries while importing the production module.
    sys.modules["hid"] = types.ModuleType("hid")

from mouse_battery_tray.attack_shark import parse_battery_packet


def fuzz_one_input(data: bytes) -> None:
    result = parse_battery_packet(list(data))
    if result is None:
        return
    battery = result["battery"]
    assert isinstance(battery, int)
    assert 0 <= battery <= 100
    assert isinstance(result["charging"], bool)
    assert isinstance(result["full"], bool)


def main() -> None:
    import atheris

    atheris.instrument_func(fuzz_one_input)
    atheris.Setup(sys.argv, fuzz_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
