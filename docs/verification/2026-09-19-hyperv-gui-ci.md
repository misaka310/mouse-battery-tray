# Hyper-V GUI acceptance — 2026-09-19

This acceptance run proves the packaged application can start and present its Settings UI inside the isolated Hyper-V GUI test environment without mouse or keyboard input injection.

## Environment

- Controller repository: `misaka310/132_hyperv-gui-ci-runner`
- Isolated guest: `GUI-CI-01`
- Clean checkpoint: `gui-clean`
- Target ref: `feature/mouse-battery-tray-generic`
- Target commit: `be92837ea4d9fa36cef30343fb25e35f6b58d0fb`
- Acceptance run: `35433576339`

## Result

The GUI target returned `PASS`.

Verified conditions:

- packaged EXE smoke test exit code: `0`
- Settings window visible: `true`
- primary tray process remained alive: `true`
- duplicate launch exited: `true`
- resulting process count: `1`
- mouse/keyboard input injection used: `false`
- screenshot captured from the guest desktop
- cleanup result: `PASS`
- forced VM shutdown required: `false`
- final restore returned the guest to `gui-clean`

Packaged executable SHA-256:

```text
ff5e664308b9e2459b7a6e502c08e8be1d7573a2f3e2a735ccc955f4255bf235
```

Screenshot SHA-256:

```text
4c73381407224ab68c0545516b40c7d7a6f37af380ac64b763220e4ec902946d
```

The screenshot committed as `docs/images/settings-vm.png` is the artifact produced by this run.

## Safety boundary

The acceptance entrypoint does not call `click_input`, `send_keys`, `pyautogui`, `pynput`, Win32 `SendInput`, `mouse_event`, `keybd_event`, or equivalent input-injection APIs.

The Settings window is opened deterministically with the application CLI flag `--show-settings`. The test observes process and window state, captures a screenshot, and terminates the packaged process without interacting with the user's real desktop.
