# Windows GUI smoke testing

The regular Windows workflow runs unit tests and builds the PyInstaller package. It does not prove that the packaged notification-area menu can be opened and operated by a user.

`powershell -File scripts/run-gui-smoke.ps1` builds the real `Mouse-Battery-Tray.exe` and operates it through Windows UI Automation. Controls are selected by accessible names and control types rather than fixed screen coordinates.

## Scenarios

- the packaged tray application starts;
- Refresh remains responsive;
- Show settings opens one responsive Settings window and it can be closed;
- Open logs opens the intended folder;
- all expected menu items exist and are enabled;
- a duplicate launch keeps one tray instance;
- Quit exits cleanly;
- the application remains operable after a second launch and exits cleanly again.

The **Start on boot** item is checked for presence and enablement, but the smoke test does not toggle it.

## GitHub Actions

The public repository runs `.github/workflows/windows-gui-smoke.yml` on GitHub-hosted `windows-latest` for pull requests and manual `workflow_dispatch` runs. No self-hosted runner, repository variable, or custom runner label is required.

The job checks out a fresh Windows runner, sets up Python, builds the PyInstaller package, and operates the real taskbar and notification-area UI. The hidden-icon overflow refresh used during relaunch is committed in `tests/windows/hosted_tray_uia_smoke.py`; the workflow does not rewrite test source at runtime.

## Local execution

The same smoke contract can be run from an interactive Windows desktop:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-gui-smoke.ps1
```

Do not run it while another packaged copy from the same checkout is already running. The test opens the tray menu, Settings window, logs folder, and hidden-icon overflow while it runs.

## Results

Success prints one `PASS` line per scenario. Failure exits non-zero and saves JSON plus a desktop screenshot under:

```text
test-results/windows-gui-smoke/
```

GitHub Actions uploads that directory only on failure.
