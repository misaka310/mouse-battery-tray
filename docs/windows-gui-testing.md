# Windows GUI verification

## Safety rule

Automated mouse/keyboard input injection is prohibited for this project.

The test suite must not use `click_input`, `send_keys`, `pyautogui`, `pynput`, Win32 `SendInput`, `mouse_event`, `keybd_event`, or equivalent APIs.

This rule exists specifically to prevent automated tests from moving the user's pointer, clicking taskbar/tray UI, changing focus, or typing into the user's active desktop session.

## Automated verification allowed on the host

The following checks are safe to automate because they do not inject user input:

- unit tests for protocol parsing and state mapping;
- HID receiver reads;
- process count / single-instance inspection;
- icon image generation;
- settings object construction and destruction;
- PyInstaller build;
- packaged `--smoke-test`;
- static checks that fail if banned input-injection APIs are added.

The repository enforces the last item in `tests/test_no_input_injection.py`.

## Interactive GUI verification

If a release requires visual confirmation of tray-menu behavior, Settings layout, or notification-area placement:

1. use a disposable VM or other desktop session that is isolated from the user's real host session;
2. perform the interaction manually;
3. do not automate the interaction with injected mouse or keyboard input;
4. record only the pass/fail result and sanitized screenshots if appropriate;
5. if an isolated VM is unavailable, mark the interactive GUI check as not run instead of running it on the host.

## CI

GitHub-hosted CI performs build, lint, typecheck, unit tests, coverage, and packaged smoke checks. It does not simulate mouse or keyboard input.
