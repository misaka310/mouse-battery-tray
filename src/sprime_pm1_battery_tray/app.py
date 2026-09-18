import time
import threading
import datetime
import pystray
from pystray import MenuItem as item
from PIL import Image
import queue
import os
import sys
import argparse
import customtkinter as ctk
import tkinter as tk

from .config import get_log_dir, load_config, save_config
from .battery_reader import get_battery_info
from .icon_renderer import create_battery_icon
from .settings_window import SettingsWindow
from .startup import is_startup_enabled, set_startup

class BatteryTrayApp:
    def __init__(self):
        self.config = load_config()
        
        # Ensure startup matches config if frozen
        if getattr(sys, 'frozen', False):
            set_startup(self.config.get("start_on_boot", False))
        
        self.current_status = {
            "device": "Mouse",
            "battery": "--",
            "status": "Initializing...",
            "last_update": "--",
            "last_error": "None",
            "charging": False,
            "full": False
        }
        
        # Event queue for thread-safe communication
        self.queue = queue.Queue()

        # HID feature reports should not be queried concurrently. Manual refresh
        # can otherwise overlap with the periodic polling thread and produce
        # access errors on some Windows HID stacks.
        self.poll_lock = threading.Lock()
        
        # UI Root
        self.root = ctk.CTk()
        self.root.withdraw()  # Hide main root window
        self.root.overrideredirect(True) # Remove from taskbar
        self.root.attributes("-alpha", 0) # Make fully transparent just in case
        ctk.set_appearance_mode("dark")

        # Components
        self.settings_window = SettingsWindow(
            self.root, 
            self.on_config_changed, 
            lambda: self.queue.put(("manual_refresh", None))
        )
        
        # Pystray Icon
        self.icon = pystray.Icon("mouse_battery_tray")
        self.update_tray_icon()
        self.icon.menu = pystray.Menu(
            item('Refresh now', lambda: self.queue.put(("manual_refresh", None))),
            item('Show settings', lambda: self.queue.put(("show_settings", None))),
            item('Start on boot', self.toggle_start_on_boot, checked=lambda item: is_startup_enabled()),
            item('Open logs', lambda: self.queue.put(("open_logs", None))),
            item('Quit', lambda: self.queue.put(("quit", None)))
        )
        
        self.running = True
        self.last_poll_time = 0
        self.notified_low_battery = False
        
        # Start queue processor
        self.process_queue()
        
        # Start HID polling thread
        self.poll_thread = threading.Thread(target=self.poll_worker, daemon=True)
        self.poll_thread.start()

    def process_queue(self):
        """Processes events from the queue in the main thread."""
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
        """Force a poll immediately."""
        threading.Thread(target=self.poll_worker, args=(True,), daemon=True).start()

    def poll_once(self):
        """Read HID battery state once, unless another read is already active."""
        if not self.poll_lock.acquire(blocking=False):
            return None
        try:
            return get_battery_info()
        finally:
            self.poll_lock.release()

    def poll_worker(self, immediate=False):
        """Background thread for HID polling."""
        if not immediate:
            # Initial delay to let UI settle
            time.sleep(1)
            
        while self.running:
            res = self.poll_once()
            if res is not None:
                self.queue.put(("update_status", res))
            
            # Wait for next interval
            interval = self.config.get("refresh_interval_sec", 300)
            if immediate:
                return # Exit if it was a manual refresh thread
                
            # Sleep in small chunks to remain responsive to quit
            for _ in range(interval * 2): # 0.5s chunks
                if not self.running: break
                time.sleep(0.5)

    def handle_update_status(self, res):
        """Updates internal status and refreshes UI components."""
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.current_status["last_update"] = now_str
        
        if "error" in res:
            self.current_status["last_error"] = res["error"]
        else:
            self.current_status["last_error"] = "None"
            
        self.current_status["device"] = res.get("device", self.current_status.get("device", "Mouse"))
        self.current_status["status"] = res.get("status", "unknown")
        
        if res.get("status") in ["connected", "disconnected"]:
            self.current_status["battery"] = res.get("battery", "--")
            self.current_status["charging"] = res.get("charging", False)
            self.current_status["full"] = res.get("full", False)
            
            if res.get("status") == "connected" and isinstance(self.current_status["battery"], int):
                # Check low battery
                thresh = self.config.get("low_battery_threshold", 20)
                if self.current_status["battery"] <= thresh and not self.current_status["charging"]:
                    if self.config.get("notify_low_battery", True) and not self.notified_low_battery:
                        self.icon.notify(
                            f"Battery is low: {self.current_status['battery']}%",
                            self.current_status.get("device", "Mouse Battery Tray"),
                        )
                        self.notified_low_battery = True
                else:
                    self.notified_low_battery = False
        
        self.update_tray_icon()
        if self.settings_window.root:
            self.settings_window.update_status(self.current_status)

    def update_tray_icon(self):
        batt = self.current_status["battery"]
        perc = batt if isinstance(batt, int) else None
        status = self.current_status["status"]
        is_charging = self.current_status.get("charging", False)
        
        # Use new icon renderer
        img = create_battery_icon(
            perc, 
            status, 
            is_charging, 
            low_battery_threshold=self.config.get("low_battery_threshold", 20)
        )
        self.icon.icon = img
        
        device = self.current_status.get("device", "Mouse")
        if status == "connected" and perc is not None:
            self.icon.title = f"{device}: {perc}%"
        elif status == "disconnected":
            self.icon.title = f"{device}: Disconnected / sleeping"
        elif status == "device_not_found":
            self.icon.title = "Mouse Battery Tray: No supported mouse"
        else:
            self.icon.title = f"{device}: {status}"

    def toggle_start_on_boot(self):
        enabled = not is_startup_enabled()
        set_startup(enabled)
        self.config["start_on_boot"] = enabled
        save_config(self.config)

    def open_logs_folder(self):
        log_dir = get_log_dir()
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        os.startfile(log_dir)

    def on_config_changed(self, new_config):
        self.config = new_config
        self.update_tray_icon()

    def quit(self):
        self.running = False
        self.icon.stop()
        self.root.quit()
        self.root.destroy()

    def run(self):
        # Start pystray icon in a background thread
        icon_thread = threading.Thread(target=self.icon.run)
        icon_thread.daemon = True
        icon_thread.start()
        
        # Run tkinter mainloop in the main thread
        self.root.mainloop()

def main():
    parser = argparse.ArgumentParser(description="Mouse Battery Tray")
    parser.add_argument("--smoke-test", action="store_true", help="Run a smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        print("Running smoke test...")
        try:
            # 1. Package import check
            import customtkinter as ctk
            import pystray
            
            # 2. Config load check
            print("Checking config...")
            config = load_config()
            
            # 3. Icon generation check
            print("Checking icon generation...")
            img = create_battery_icon(50, "connected", False)
            if img is None:
                print("Error: Icon generation failed")
                sys.exit(1)
                
            # 4. HID read check
            print("Checking HID reading...")
            res = get_battery_info()
            print(f"HID Result: {res}")
            
            # 5. UI initialization check (partial)
            print("Checking UI initialization...")
            root = ctk.CTk()
            settings = SettingsWindow(root, lambda x: None, lambda: None)
            root.destroy()
            
            print("Smoke test passed!")
            sys.exit(0)
            
        except Exception as e:
            print(f"Smoke test failed with error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    app = BatteryTrayApp()
    app.run()

if __name__ == "__main__":
    main()
