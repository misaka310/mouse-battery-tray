from sprime_pm1_battery_tray.icon_renderer import create_battery_icon


def pixel(image):
    return image.getpixel((1, 1))


def test_create_battery_icon_states():
    connected = create_battery_icon(50, "connected", False)
    disconnected = create_battery_icon(None, "disconnected", False)
    charging = create_battery_icon(100, "connected", True)
    charging_unknown = create_battery_icon(None, "connected", True)
    error = create_battery_icon(None, "read_failed", False)

    for image in (connected, disconnected, charging, charging_unknown, error):
        assert image.size == (32, 32)
        assert image.mode == "RGBA"

    assert pixel(charging_unknown) != pixel(disconnected)
    assert pixel(error) != pixel(disconnected)
