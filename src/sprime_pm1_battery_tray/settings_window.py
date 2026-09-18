import os
import tkinter as tk

import customtkinter as ctk

from .config import get_log_dir, load_config, save_config
from .startup import is_startup_enabled, set_startup

PREFERRED_LABELS = {
    "auto": "Auto",
    "attack_shark_x1": "ATTACK SHARK X1",
    "sprime_pm1": "SPRIME PM1",
}
PREFERRED_KEYS = {label: key for key, label in PREFERRED_LABELS.items()}


class SettingsWindow:
    def __init__(self, master, on_config_changed, on_manual_refresh):
        self.master = master
        self.root = None
        self.on_config_changed = on_config_changed
        self.on_manual_refresh = on_manual_refresh
        self.config = load_config()
        self.status_labels = {}

    def show(self, current_status):
        if self.root is not None:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            return

        self.config = load_config()
        self.root = ctk.CTkToplevel(self.master)
        self.root.title("Mouse Battery Tray Settings")
        self.root.geometry("470x620")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        ctk.set_appearance_mode("dark")

        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(main_frame, text="Mouse Battery Tray", font=("Inter", 24, "bold")).pack(
            pady=(0, 20), anchor="w"
        )

        status_card = ctk.CTkFrame(
            main_frame, corner_radius=12, border_width=1, border_color="#333333"
        )
        status_card.pack(fill="x", pady=(0, 20))
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(padx=15, pady=15, fill="x")

        fields = [
            ("Device", "device"),
            ("Battery", "battery"),
            ("Status", "status"),
            ("Last Update", "last_update"),
            ("Last Error", "last_error"),
        ]
        for index, (label, key) in enumerate(fields):
            ctk.CTkLabel(
                status_inner,
                text=f"{label}:",
                font=("Inter", 12, "bold"),
                text_color="#aaaaaa",
            ).grid(row=index, column=0, sticky="w", pady=2)
            value_label = ctk.CTkLabel(status_inner, text="--", font=("Inter", 12))
            value_label.grid(row=index, column=1, sticky="w", padx=10, pady=2)
            self.status_labels[key] = value_label

        self.update_status(current_status)
        ctk.CTkButton(
            status_inner,
            text="Refresh Now",
            command=self.on_manual_refresh,
            height=32,
            corner_radius=8,
        ).grid(row=len(fields), column=0, columnspan=2, pady=(15, 0), sticky="ew")

        ctk.CTkLabel(main_frame, text="Settings", font=("Inter", 16, "bold")).pack(
            pady=(0, 10), anchor="w"
        )
        settings_card = ctk.CTkFrame(
            main_frame, corner_radius=12, border_width=1, border_color="#333333"
        )
        settings_card.pack(fill="both", expand=True)
        settings_inner = ctk.CTkFrame(settings_card, fg_color="transparent")
        settings_inner.pack(padx=15, pady=15, fill="both", expand=True)

        device_frame = ctk.CTkFrame(settings_inner, fg_color="transparent")
        device_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(device_frame, text="Preferred mouse:", font=("Inter", 13)).pack(side="left")
        preferred_key = self.config.get("preferred_device", "auto")
        self.var_device = tk.StringVar(value=PREFERRED_LABELS.get(preferred_key, "Auto"))
        ctk.CTkOptionMenu(
            device_frame,
            variable=self.var_device,
            values=list(PREFERRED_KEYS),
            command=lambda _value: self.save(),
            width=190,
        ).pack(side="right")

        self.var_boot = tk.BooleanVar(value=is_startup_enabled())
        ctk.CTkCheckBox(
            settings_inner,
            text="Start on boot",
            variable=self.var_boot,
            command=self.save,
            font=("Inter", 13),
        ).pack(anchor="w", pady=5)

        self.var_notify = tk.BooleanVar(value=self.config.get("notify_low_battery", True))
        ctk.CTkCheckBox(
            settings_inner,
            text="Low battery notification",
            variable=self.var_notify,
            command=self.save,
            font=("Inter", 13),
        ).pack(anchor="w", pady=5)

        interval_frame = ctk.CTkFrame(settings_inner, fg_color="transparent")
        interval_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(interval_frame, text="Refresh interval (sec):", font=("Inter", 13)).pack(side="left")
        self.var_interval = tk.StringVar(value=str(self.config.get("refresh_interval_sec", 300)))
        interval_entry = ctk.CTkEntry(interval_frame, textvariable=self.var_interval, width=60, height=24)
        interval_entry.pack(side="right")
        interval_entry.bind("<FocusOut>", lambda _event: self.save())
        interval_entry.bind("<Return>", lambda _event: self.save())

        threshold_frame = ctk.CTkFrame(settings_inner, fg_color="transparent")
        threshold_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(
            threshold_frame, text="Low battery threshold (%):", font=("Inter", 13)
        ).pack(side="left")
        self.var_thresh = tk.StringVar(value=str(self.config.get("low_battery_threshold", 20)))
        threshold_entry = ctk.CTkEntry(threshold_frame, textvariable=self.var_thresh, width=60, height=24)
        threshold_entry.pack(side="right")
        threshold_entry.bind("<FocusOut>", lambda _event: self.save())
        threshold_entry.bind("<Return>", lambda _event: self.save())

        actions_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(20, 0))
        ctk.CTkButton(
            actions_frame,
            text="Open Logs",
            command=self.open_logs,
            fg_color="#333333",
            hover_color="#444444",
            width=100,
        ).pack(side="left")
        ctk.CTkButton(actions_frame, text="Close", command=self.on_close, width=100).pack(side="right")

    def update_status(self, current_status):
        if not self.root:
            return
        battery = current_status.get("battery", "--")
        self.status_labels["device"].configure(text=current_status.get("device", "Mouse"))
        self.status_labels["battery"].configure(
            text=f"{battery}%" if isinstance(battery, int) else str(battery)
        )
        self.status_labels["status"].configure(text=current_status.get("status", "unknown"))
        self.status_labels["last_update"].configure(text=current_status.get("last_update", "--"))
        self.status_labels["last_error"].configure(text=current_status.get("last_error", "None"))

    def save(self):
        try:
            interval = max(5, int(self.var_interval.get()))
        except (TypeError, ValueError):
            interval = 300
        try:
            threshold = min(100, max(0, int(self.var_thresh.get())))
        except (TypeError, ValueError):
            threshold = 20

        self.config["refresh_interval_sec"] = interval
        self.config["low_battery_threshold"] = threshold
        self.config["notify_low_battery"] = self.var_notify.get()
        self.config["preferred_device"] = PREFERRED_KEYS.get(self.var_device.get(), "auto")

        start_on_boot = self.var_boot.get()
        self.config["start_on_boot"] = start_on_boot
        set_startup(start_on_boot)

        save_config(self.config)
        self.on_config_changed(dict(self.config))

    def open_logs(self):
        log_dir = get_log_dir()
        os.makedirs(log_dir, exist_ok=True)
        os.startfile(log_dir)

    def on_close(self):
        if self.root:
            self.root.destroy()
            self.root = None
