# Changelog

All notable user-visible changes are documented here.

## Unreleased

### Added

- Generic `Mouse Battery Tray` device layer with automatic ATTACK SHARK X1 / SPRIME PM1 selection.
- ATTACK SHARK X1 2.4 GHz receiver support verified against real hardware.
- Architecture, protocol, verification, contribution, security, and third-party documentation.
- Windows GUI smoke workflow and packaged EXE smoke validation.
- Recruiter-facing architecture and verification diagrams.

### Changed

- Renamed the internal Python package from `sprime_pm1_battery_tray` to `mouse_battery_tray`.
- Build artifact and installed application are named `Mouse-Battery-Tray`.
- CI now uses read-only permissions for verification; write permission is isolated to tagged releases.
- Setup ignores the Windows Store `python.exe` execution alias and searches for a real Python installation.

### Compatibility

- Existing SPRIME PM1 configuration is migrated to the generic application data directory.
- ATTACK SHARK X1 is verified only for the 2.4 GHz receiver path documented in `docs/protocol-notes.md`.
