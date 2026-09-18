import json
import os

import hid

SUPPORTED_RECEIVERS = {
    (0x1D57, 0xFA60): "ATTACK SHARK X1 / compatible 2.4G receiver",
    (0x1915, 0xAC1C): "SPRIME PM1",
}


def scan_devices():
    return hid.enumerate()


def get_supported_candidates(devices):
    candidates = []
    for device in devices:
        key = (int(device.get("vendor_id", 0)), int(device.get("product_id", 0)))
        if key in SUPPORTED_RECEIVERS:
            row = dict(device)
            row["detected_model"] = SUPPORTED_RECEIVERS[key]
            candidates.append(row)
    return candidates


def dump_devices(devices, log_path_json, log_path_txt):
    os.makedirs(os.path.dirname(log_path_json), exist_ok=True)

    serializable_devices = []
    for device in devices:
        row = dict(device)
        if isinstance(row.get("path"), bytes):
            row["path"] = row["path"].decode("ascii", errors="ignore")
        serializable_devices.append(row)

    with open(log_path_json, "w", encoding="utf-8") as handle:
        json.dump(serializable_devices, handle, indent=4, ensure_ascii=False)

    with open(log_path_txt, "w", encoding="utf-8") as handle:
        for device in devices:
            path = device.get("path")
            if isinstance(path, bytes):
                path = path.decode("ascii", errors="ignore")
            handle.write(
                "VID: 0x{vid:04x}, PID: 0x{pid:04x}, Mfr: {mfr}, Prod: {prod}, "
                "Ser: {serial}, Interface: {interface}, UsagePage: 0x{usage_page:04x}, "
                "Usage: 0x{usage:04x}, Path: {path}\n".format(
                    vid=int(device.get("vendor_id", 0)),
                    pid=int(device.get("product_id", 0)),
                    mfr=device.get("manufacturer_string"),
                    prod=device.get("product_string"),
                    serial=device.get("serial_number"),
                    interface=device.get("interface_number"),
                    usage_page=int(device.get("usage_page", 0)),
                    usage=int(device.get("usage", 0)),
                    path=path,
                )
            )


if __name__ == "__main__":
    devices = scan_devices()
    dump_devices(devices, "logs/hid-devices.json", "logs/hid-devices.txt")
    candidates = get_supported_candidates(devices)
    print(f"Found {len(devices)} HID devices.")
    print(f"Found {len(candidates)} supported receiver endpoints.")
    for candidate in candidates:
        print(
            "- {model}: VID 0x{vid:04x}, PID 0x{pid:04x}, interface {interface}, "
            "usage page 0x{usage_page:04x}".format(
                model=candidate["detected_model"],
                vid=int(candidate.get("vendor_id", 0)),
                pid=int(candidate.get("product_id", 0)),
                interface=candidate.get("interface_number"),
                usage_page=int(candidate.get("usage_page", 0)),
            )
        )
