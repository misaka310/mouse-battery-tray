## Summary

Describe the user-visible or protocol-level change.

## Verification

- [ ] `ruff check src tests`
- [ ] `pytest tests`
- [ ] PyInstaller build succeeds
- [ ] Packaged EXE smoke test succeeds
- [ ] If hardware support changed, real-device evidence is included

## Hardware evidence

For device-support changes, include model, connection mode, VID/PID, endpoint details, and a sanitized raw report. Do not include serial numbers or personal paths.

## Scope

- [ ] I did not mark an untested device as verified.
- [ ] Device-specific logic stays behind a protocol adapter instead of leaking into the tray UI.
