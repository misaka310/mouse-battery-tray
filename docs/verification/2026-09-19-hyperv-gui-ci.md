# Hyper-V GUI acceptance — 2026-09-19

This acceptance run proves the packaged application can start and present its Settings UI inside the isolated Hyper-V GUI test environment without mouse or keyboard input injection.

## Environment

- Controller repository: `misaka310/132_hyperv-gui-ci-runner`
- Controller branch: `main`
- Isolated guest: `GUI-CI-01`
- Clean checkpoint: `gui-clean`
- Target repository: `misaka310/mouse-battery-tray`
- Target ref: `main`
- Target commit: `247a238a1e7a091545425f83a58238fe7eaf2d14`
- Acceptance run: `35445742282`

## Result

The complete workflow returned `success`:

- `start-vm`: `success`
- `gui-test`: `success`
- `stop-vm`: `success`

Verified target conditions:

- packaged EXE smoke test exit code: `0`
- Settings window visible: `true`
- primary tray process remained alive: `true`
- duplicate launch exited: `true`
- resulting process count: `1`
- mouse/keyboard input injection used: `false`
- screenshot captured from the isolated guest desktop
- cleanup result: `PASS`
- forced VM shutdown required: `false`
- final restore returned the guest to `gui-clean`

Packaged executable SHA-256:

```text
11dc5928cf69bae7f7a5b05891cc67ab01913ed37cc061878754b0942b6772e6
```

Screenshot SHA-256:

```text
7493cdeaadd421bc9b1146f0d82a1514f2fba77ab87def645c85d08160ea85f6
```

The screenshot committed as `docs/images/settings-vm.png` is the artifact produced by this final `main` acceptance run.

## Cleanup diagnostic

The cleanup contract returned `PASS` and did not require a forced shutdown. Its bounded host-memory recovery probe recorded a diagnostic warning because commit headroom had not returned within the configured tolerance before the deadline:

- free physical memory: `41,441 MB`
- commit headroom: `52,647 MB`
- `recovery.healthy`: `false`

The 132 controller intentionally treats this recovery shortfall as a diagnostic warning rather than a VM-cleanup failure. Start admission remains based on the current free-memory and commit-headroom checks, and the lease was removed after cleanup.

## Safety boundary

The acceptance entrypoint does not call `click_input`, `send_keys`, `pyautogui`, `pynput`, Win32 `SendInput`, `mouse_event`, `keybd_event`, or equivalent input-injection APIs.

The Settings window is opened deterministically with the application CLI flag `--show-settings`. The test observes process and window state, captures a screenshot, and terminates the packaged process without interacting with the user's real desktop.
