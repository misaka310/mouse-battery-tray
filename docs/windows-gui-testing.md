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

## Isolated GUI verification

Visual checks run only in a desktop session isolated from the user's real host session. The current acceptance environment is the Hyper-V runner `GUI-CI-01` managed by repository `132_hyperv-gui-ci-runner`.

The automated acceptance path is deliberately non-interactive:

1. restore the VM to `gui-clean`;
2. stage the allowlisted repository at an exact commit;
3. build the packaged EXE inside the guest;
4. start the EXE with `--show-settings`;
5. verify the Settings top-level window exists;
6. start a duplicate instance and verify the process count remains one;
7. capture the guest desktop as evidence;
8. terminate the test process;
9. stop the VM and restore `gui-clean`.

No mouse or keyboard events are synthesized. If a release requires a control to be clicked or text to be entered, that step is a human-only check inside the isolated VM. If an isolated VM is unavailable, the check is marked not run instead of being moved to the host.

## CI

GitHub-hosted CI performs build, lint, typecheck, unit tests, coverage, and packaged smoke checks. The isolated Hyper-V acceptance path adds visual Settings verification and screenshot evidence. Neither path simulates mouse or keyboard input. See [the 2026-09-19 acceptance record](verification/2026-09-19-hyperv-gui-ci.md).
