from mouse_battery_tray import hid_scan


def test_supported_candidates_only_include_active_x1_receiver():
    devices = [
        {"vendor_id": 0x1D57, "product_id": 0xFA60, "path": b"x1"},
        {"vendor_id": 0x1915, "product_id": 0xAC1C, "path": b"retired-pm1"},
    ]

    candidates = hid_scan.get_supported_candidates(devices)

    assert len(candidates) == 1
    assert candidates[0]["path"] == b"x1"
    assert candidates[0]["detected_model"] == "ATTACK SHARK X1 / compatible 2.4G receiver"
