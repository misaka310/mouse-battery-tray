import argparse
import datetime
import os
import queue
import sys
import threading
import time

import customtkinter as ctk
import pystray
from pystray import MenuItem as item

from .config import get_log_dir, load_config, save_config
from .device_manager import DeviceManager
from .icon_renderer import create_battery_icon
from .settings_window import SettingsWindow
from .startup import is_startup_enabled, set_startup


class BatteryTrayApp:
    def __init__(self, device_manager=None):
        self.config = load_config()
        self.device_manager = device_manager or DeviceManager()

        # Keep persisted startup preference and actual registry state aligned.
        if getattr(sys, "frozen", False):
            set_startup(self.config.get("start_on_boot", False))

        self.current_status = {
            "device": "Mouse",
            "device_key": "auto",
            "battery": "--",
            "status": "Initializing...",
            "last_update": "--",
            "last_error": "None",
            "charging": False,
            "full": False,
        }

        self.queue = queue.Queue()
        self.poll_lock = threading.Lock()

        self.root = ctk.CTk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0)
        ctk.set_appearance_mode("dark")

        self.settings_window = SettingsWindow(
            self.root,
            self.on_config_changed,
            lambda: self.queue.put(("manual_refresh", None)),
        )

        self.icon = pystray.Icon("mouse_battery_tray")
        self.update_tray_icon()
        self.icon.menu = pystray.Menu(
            item("Refresh now", lambda: self.queue.put(("manual_refresh", None))),
            item("Show settings", lambda: self.queue.put(("show_settings", None))),
            item("Start on boot", self.toggle_start_on_boot, checked=lambda item: is_startup_enabled()),
            item("Open logs", lambda: self.queue.put(("open_logs", None))),
            item("Quit", lambda: self.queue.put(("quit", None))),
        )

        self.running = True
        self.notified_low_battery = False

        self.process_queue()
        self.poll_thread = threading.Thread(target=self.poll_worker, daemon=True)
        self.poll_thread.start()

    def process_queue(self):
        """Process cross-thread events on the Tk main thread."""
        try:
            while True:
                msg, data = self.queue.get_nowait()
                if msg == "update_status":
                    self.handle_update_status(data)
                elif msg == "show_settings":
                    self.settings_window.show(self.current_status)
                elif msg == "manual_refresh":
                    self.trigger_refresh()
                elif msg == "open_logs":
                    self.open_logs_folder()
                elif msg == "quit":
                    self.quit()
                    return
                self.queue.task_done()
        except queue.Empty:
            pass

        if self.running:
            self.root.after(100, self.process_queue)

    def trigger_refresh(self):
        """Force a poll immediately without overlapping another HID read."""
        threading.Thread(target=self.poll_worker, args=(True,), daemon=True).start()

    def poll_once(self):
        """Read the selected supported mouse once, unless another read is active."""
        if not self.poll_lock.acquire(blocking=False):
            return None
        try:
            return self.device_manager.get_battery_info(
                self.config.get("preferred_device", "auto")
            )
        finally:
            self.poll_lock.release()

    def poll_worker(self, immediate=False):
        """Background HID polling with device-specific refresh recommendations."""
        if not immediate:
            time.sleep(1)

        while self.running:
            result = self.poll_once()
            if result is not None:
                self.queue.put(("update_status", result))

            if immediate:
                return

            configured = max(5, int(self.config.get("refresh_interval_sec", 300)))
            recommended = result.get("recommended_refresh_sec") if isinstance(result, dict) else None
            if isinstance(recommended, (int, float)) and recommended > 0:
                interval = min(configured, float(recommended))
            elif isinstance(result, dict) and result.get("status") in {
                "device_not_found",
                "disconnected",
                "read_failed",
                "enumeration_failed",
                "permission_or_access_error",
            }:
                interval = min(configured, 5.0)
            else:
                interval = float(configured)

            deadline = time.monotonic() + interval
            while self.running and time.monotonic() < deadline:
                time.sleep(min(0.5, max(0.05, deadline - time.monotonic())))

    def handle_update_status(self, result):
        """Update internal state and both tray/settings UI."""
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.current_status["last_update"] = now_str
        self.current_status["last_error"] = result.get("error", "None")
        self.current_status["status"] = result.get("status", "unknown")
        self.current_status["device"] = result.get("device", self.current_status.get("device", "Mouse"))
        self.current_status["device_key"] = result.get(
            "device_key", self.current_status.get("device_key", "auto")
        )

        status = result.get("status")
        if status in {"connected", "disconnected"}:
            battery = result.get("battery")
            self.current_status["battery"] = battery if isinstance(battery, int) else "--"
            self.current_status["charging"] = bool(result.get("charging", False))
            self.current_status["full"] = bool(result.get("full", False))

            if status == "connected" and isinstance(battery, int):
                threshold = int(self.config.get("low_battery_threshold", 20))
                if battery <= threshold and not self.current_status["charging"]:
                    if self.config.get("notify_low_battery", True) and not self.notified_low_battery:
                        self.icon.notify(
                            f"Battery is low: {battery}%",
                            self.current_status["device"],
                        )
                        self.notified_low_battery = True
                else:
                    self.notified_low_battery = False
        else:
            self.current_status["battery"] = "--"
            self.current_status["charging"] = False
            self.current_status["full"] = False

        self.update_tray_icon()
        if self.settings_window.root:
            self.settings_window.update_status(self.current_status)

    def update_tray_icon(self):
        battery = self.current_status["battery"]
        percentage = battery if isinstance(battery, int) else None
        status = self.current_status["status"]
        is_charging = self.current_status.get("charging", False)

        self.icon.icon = create_battery_icon(
            percentage,
            status,
            is_charging,
            low_battery_threshold=self.config.get("low_battery_threshold", 20),
        )

        device = self.current_status.get("device") or "Mouse"
        if status == "connected" and percentage is not None:
            suffix = " (charging)" if is_charging else ""
            self.icon.title = f"{device}: {percentage}%{suffix}"
        elif status == "connected" and is_charging:
            self.icon.title = f"{device}: Charging (battery unavailable)"
        elif status in {"disconnected", "device_not_found"}:
            self.icon.title = f"{device}: Disconnected"
        else:
            self.icon.title = f"{device}: {status}"

    def toggle_start_on_boot(self):
        enabled = not is_startup_enabled()
        set_startup(enabled)
        self.config["start_on_boot"] = enabled
        save_config(self.config)

    def open_logs_folder(self):
        log_dir = get_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        os.startfile(log_dir)

    def on_config_changed(self, new_config):
        self.config = new_config
        self.update_tray_icon()
        self.queue.put(("manual_refresh", None))

    def quit(self):
        self.running = False
        try:
            self.device_manager.close()
        except Exception:
            pass
        self.icon.stop()
        self.root.quit()
        self.root.destroy()

    def run(self):
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Mouse Battery Tray")
    parser.add_argument("--smoke-test", action="store_true", help="Run a smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        print("Running smoke test...")
        manager = DeviceManager()
        try:
            print("Checking config...")
            load_config()

            print("Checking icon generation...")
            image = create_battery_icon(50, "connected", False)
            if image is None:
                print("Error: Icon generation failed")
                sys.exit(1)

            print("Checking HID reading...")
            result = manager.get_battery_info("auto")
            print(f"HID Result: {result}")

            print("Checking UI initialization...")
            root = ctk.CTk()
            SettingsWindow(root, lambda value: None, lambda: None)
            root.destroy()

            print("Smoke test passed!")
            sys.exit(0)
        except Exception as exc:
            print(f"Smoke test failed with error: {exc}")
            import traceback

            traceback.print_exc()
            sys.exit(1)
        finally:
            manager.close()

    BatteryTrayApp().run()


if __name__ == "__main__":
    main()
