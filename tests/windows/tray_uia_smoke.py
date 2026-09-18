from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import os
import subprocess
import time
import traceback
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import psutil
import win32com.client
from PIL import ImageGrab
from pywinauto import Desktop

APP_NAME = "Mouse Battery Tray"
EXE = Path(os.environ["GUI_SMOKE_EXE"]).resolve()
PACKAGE_ROOT = EXE.parent
LOGS_DIR = PACKAGE_ROOT / "logs"
RESULT_DIR = Path(os.environ.get("GUI_SMOKE_RESULT_DIR", Path.cwd() / "test-results" / "windows-gui-smoke"))
EXPECTED_ACTIONS = (
    "Refresh now",
    "Show settings",
    "Start on boot",
    "Open logs",
    "Quit",
)

USER32 = ctypes.windll.user32
WM_CLOSE = 0x0010
WM_NULL = 0x0000
SMTO_ABORTIFHUNG = 0x0002


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    pid: int
    title: str
    class_name: str


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    detail: str = ""


def wait_until(description: str, predicate: Callable[[], object], timeout: float = 10.0, interval: float = 0.2):
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except Exception as exc:
            last_error = exc
        time.sleep(interval)
    suffix = f"; last error: {last_error}" if last_error else ""
    raise TimeoutError(f"Timed out waiting for {description}{suffix}")


def enum_top_windows() -> list[WindowInfo]:
    rows: list[WindowInfo] = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def callback(hwnd: int, _lparam: int) -> bool:
        title_length = USER32.GetWindowTextLengthW(hwnd)
        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        USER32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
        class_buffer = ctypes.create_unicode_buffer(256)
        USER32.GetClassNameW(hwnd, class_buffer, len(class_buffer))
        pid = wt.DWORD()
        USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rows.append(WindowInfo(int(hwnd), int(pid.value), title_buffer.value, class_buffer.value))
        return True

    USER32.EnumWindows(enum_proc(callback), 0)
    return rows


def controller_processes() -> list[psutil.Process]:
    marker = os.path.normcase(str(EXE))
    rows: list[psutil.Process] = []
    for process in psutil.process_iter(["pid", "exe"]):
        try:
            executable = process.info.get("exe")
            if executable and os.path.normcase(os.path.abspath(executable)) == marker:
                rows.append(process)
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            continue
    return sorted(rows, key=lambda item: item.pid)


def launch_app() -> psutil.Process:
    subprocess.Popen(
        [str(EXE)],
        cwd=PACKAGE_ROOT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    def find_single_process() -> psutil.Process | None:
        found = controller_processes()
        return found[0] if len(found) == 1 else None

    return wait_until("one packaged tray process", find_single_process, timeout=15)


def candidate_scopes() -> Iterable[object]:
    desktop = Desktop(backend="uia")
    taskbar = desktop.window(class_name="Shell_TrayWnd")
    if taskbar.exists(timeout=1):
        yield taskbar
    for class_name in ("TopLevelWindowForOverflowXamlIsland", "NotifyIconOverflowWindow"):
        window = desktop.window(class_name=class_name)
        if window.exists(timeout=0.5) and window.is_visible():
            yield window


def find_button(scopes: Iterable[object], predicate: Callable[[str], bool]):
    for scope in scopes:
        try:
            buttons = scope.descendants(control_type="Button")
        except Exception:
            continue
        for button in buttons:
            try:
                if predicate(button.window_text().strip()):
                    return button
            except Exception:
                continue
    return None


def open_hidden_icons_if_needed() -> None:
    taskbar = Desktop(backend="uia").window(class_name="Shell_TrayWnd")
    if not taskbar.exists(timeout=2):
        raise RuntimeError("Windows taskbar was not found; use a logged-in interactive runner session")

    def predicate(text: str) -> bool:
        lowered = text.casefold()
        return "hidden icon" in lowered or "show hidden" in lowered or "非表示のアイコン" in text

    button = find_button((taskbar,), predicate)
    if button is not None:
        button.click_input()
        time.sleep(0.7)


def find_tray_button():
    def predicate(text: str) -> bool:
        return text.casefold().startswith(APP_NAME.casefold())

    button = find_button(candidate_scopes(), predicate)
    if button is not None:
        return button
    open_hidden_icons_if_needed()
    return wait_until(
        "Mouse Battery Tray icon",
        lambda: find_button(candidate_scopes(), predicate),
        timeout=8,
    )


def find_popup(pid: int) -> WindowInfo | None:
    return next(
        (
            row
            for row in enum_top_windows()
            if row.pid == pid and row.class_name == "#32768" and USER32.IsWindowVisible(row.hwnd)
        ),
        None,
    )


def close_popup(hwnd: int) -> None:
    if USER32.IsWindow(hwnd):
        USER32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        time.sleep(0.2)


def open_menu(pid: int):
    find_tray_button().click_input(button="right")
    popup = wait_until("pystray menu", lambda: find_popup(pid), timeout=5)
    wrapper = Desktop(backend="uia").window(handle=popup.hwnd)
    wait_until("tray menu items", lambda: wrapper.descendants(control_type="MenuItem"), timeout=3)
    return popup, wrapper


def menu_items(wrapper) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in wrapper.descendants(control_type="MenuItem"):
        text = item.window_text().strip()
        if text:
            result[text] = item
    return result


def assert_menu_contract(pid: int) -> None:
    popup, wrapper = open_menu(pid)
    try:
        items = menu_items(wrapper)
        missing = [title for title in EXPECTED_ACTIONS if title not in items]
        if missing:
            raise AssertionError(f"missing menu actions: {missing}; actual={sorted(items)}")
        disabled = [title for title in EXPECTED_ACTIONS if not items[title].is_enabled()]
        if disabled:
            raise AssertionError(f"unexpected disabled actions: {disabled}")
    finally:
        close_popup(popup.hwnd)


def click_menu_item(pid: int, title: str) -> None:
    popup, wrapper = open_menu(pid)
    item = menu_items(wrapper).get(title)
    if item is None:
        close_popup(popup.hwnd)
        raise AssertionError(f"menu item not found: {title}")
    if not item.is_enabled():
        close_popup(popup.hwnd)
        raise AssertionError(f"menu item is disabled: {title}")
    item.click_input()
    wait_until("tray menu to close", lambda: not USER32.IsWindow(popup.hwnd), timeout=5)


def settings_window(pid: int) -> WindowInfo | None:
    return next(
        (
            row
            for row in enum_top_windows()
            if row.pid == pid and row.title == "Mouse Battery Tray Settings" and USER32.IsWindowVisible(row.hwnd)
        ),
        None,
    )


def assert_window_responsive(hwnd: int) -> None:
    result = ctypes.c_size_t()
    ok = USER32.SendMessageTimeoutW(hwnd, WM_NULL, 0, 0, SMTO_ABORTIFHUNG, 2000, ctypes.byref(result))
    if not ok:
        raise AssertionError(f"window {hwnd} is not responding")


def verify_settings(pid: int) -> None:
    click_menu_item(pid, "Show settings")
    window = wait_until("Mouse Battery Tray Settings window", lambda: settings_window(pid), timeout=8)
    assert_window_responsive(window.hwnd)
    USER32.PostMessageW(window.hwnd, WM_CLOSE, 0, 0)
    wait_until("settings window to close", lambda: settings_window(pid) is None, timeout=8)
    assert_menu_contract(pid)


def verify_refresh(pid: int) -> None:
    click_menu_item(pid, "Refresh now")
    time.sleep(1)
    if not psutil.pid_exists(pid):
        raise AssertionError("Refresh now terminated the tray process")
    assert_menu_contract(pid)


def normalize_path(value: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(value))).replace("/", "\\")


def shell_windows_by_path() -> dict[str, object]:
    result: dict[str, object] = {}
    shell = win32com.client.Dispatch("Shell.Application")
    for window in shell.Windows():
        try:
            location_url = str(window.LocationURL or "")
            if not location_url.lower().startswith("file:"):
                continue
            parsed = urllib.parse.urlparse(location_url)
            path = urllib.request.url2pathname(urllib.parse.unquote(parsed.path))
            if path.startswith("\\") and len(path) > 3 and path[2] == ":":
                path = path[1:]
            result[normalize_path(path)] = window
        except Exception:
            continue
    return result


def verify_open_logs(pid: int) -> None:
    before = set(shell_windows_by_path())
    click_menu_item(pid, "Open logs")
    target = normalize_path(LOGS_DIR)
    window = wait_until("Explorer logs folder", lambda: shell_windows_by_path().get(target), timeout=10)
    if target not in before:
        try:
            window.Quit()
        except Exception:
            pass


def verify_duplicate_launch() -> int:
    subprocess.Popen(
        [str(EXE)],
        cwd=PACKAGE_ROOT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    time.sleep(2)
    rows = controller_processes()
    if len(rows) != 1:
        raise AssertionError(f"duplicate launch created {len(rows)} tray processes: {[item.pid for item in rows]}")
    return rows[0].pid


def verify_quit(pid: int) -> None:
    click_menu_item(pid, "Quit")
    wait_until("tray process exit", lambda: not controller_processes(), timeout=15)


def save_result(results: list[ScenarioResult], error: BaseException | None = None) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"ok": error is None, "results": [asdict(result) for result in results]}
    if error is not None:
        payload["error"] = f"{type(error).__name__}: {error}"
        payload["traceback"] = traceback.format_exc()
        try:
            ImageGrab.grab(all_screens=True).save(RESULT_DIR / "failure.png")
        except Exception:
            pass
    (RESULT_DIR / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_scenario(results: list[ScenarioResult], name: str, action: Callable[[], object]):
    try:
        value = action()
    except Exception as exc:
        results.append(ScenarioResult(name, False, str(exc)))
        print(f"FAIL {name}: {exc}", flush=True)
        raise
    results.append(ScenarioResult(name, True))
    print(f"PASS {name}", flush=True)
    return value


def cleanup() -> None:
    processes = controller_processes()
    for process in processes:
        try:
            process.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(processes, timeout=5)
    for process in alive:
        try:
            process.kill()
        except psutil.NoSuchProcess:
            pass


def main() -> int:
    if os.name != "nt":
        print("FAIL environment: Windows is required", flush=True)
        return 2
    if not EXE.is_file():
        print(f"FAIL environment: missing {EXE}", flush=True)
        return 2
    if controller_processes():
        print("FAIL environment: this packaged tray application is already running", flush=True)
        return 2

    results: list[ScenarioResult] = []
    try:
        process = launch_app()
        pid = process.pid
        run_scenario(results, "packaged tray starts", lambda: None)
        run_scenario(results, "tray menu contract", lambda: assert_menu_contract(pid))
        run_scenario(results, "refresh remains responsive", lambda: verify_refresh(pid))
        run_scenario(results, "settings opens and remains responsive", lambda: verify_settings(pid))
        run_scenario(results, "logs folder opens", lambda: verify_open_logs(pid))
        pid = run_scenario(results, "single instance after duplicate launch", verify_duplicate_launch)
        run_scenario(results, "clean quit", lambda: verify_quit(pid))

        second = launch_app()
        run_scenario(results, "second launch remains operable", lambda: assert_menu_contract(second.pid))
        run_scenario(results, "second clean quit", lambda: verify_quit(second.pid))
        save_result(results)
        return 0
    except Exception as exc:
        save_result(results, exc)
        return 1
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
