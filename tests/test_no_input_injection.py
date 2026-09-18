from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Code-level input injection is forbidden in this repository. GUI interaction
# that requires real input must be documented as a manual VM-only check.
BANNED_PATTERNS = {
    "click_input(": "pywinauto real-input injection",
    "send_keys(": "keyboard injection",
    "pyautogui": "mouse/keyboard injection library",
    "pynput": "mouse/keyboard injection library",
    "SendInput": "Win32 input injection",
    "mouse_event": "Win32 mouse injection",
    "keybd_event": "Win32 keyboard injection",
}

SCAN_ROOTS = (
    ROOT / "src",
    ROOT / "scripts",
    ROOT / "tests",
)

TEXT_SUFFIXES = {".py", ".ps1", ".bat", ".cmd", ".yml", ".yaml", ".toml", ".txt"}


def test_repository_contains_no_input_injection() -> None:
    violations: list[str] = []

    for scan_root in SCAN_ROOTS:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, description in BANNED_PATTERNS.items():
                if pattern in text:
                    violations.append(f"{path.relative_to(ROOT)}: {description} ({pattern})")

    assert not violations, "Input-injection code is forbidden:\n" + "\n".join(violations)
