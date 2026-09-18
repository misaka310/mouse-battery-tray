# Mouse Battery Tray (custom build)

Generic Windows tray battery monitor based on [incconutwo/mouse-battery-tray](https://github.com/incconutwo/mouse-battery-tray), extended with SPRIME PM1 support.

Verified target devices for this fork:

- ATTACK SHARK X1 — 2.4 GHz receiver VID `0x1D57`, PID `0xFA60`
- SPRIME PM1 — VID `0x1915`, PID `0xAC1C`, Feature Report `0x05`

The tray icon shows a large battery percentage. X1 uses the Beken/OEM passive packet path from the upstream project; PM1 uses the existing active Feature Report query from this repository.

Build with `scripts\build_generic.ps1`. Output: `dist\Mouse-Battery-Tray\Mouse-Battery-Tray.exe`.
