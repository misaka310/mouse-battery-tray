
from mouse_battery_tray.icon_renderer import create_battery_icon


def test_create_battery_icon():
    # Connected
    img_connected = create_battery_icon(50, "connected", False)
    assert img_connected.size == (32, 32)
    assert img_connected.mode == "RGBA"

    # Disconnected
    img_disconnected = create_battery_icon(None, "disconnected", False)
    assert img_disconnected.size == (32, 32)
    
    # Charging
    img_charging = create_battery_icon(100, "connected", True)
    assert img_charging.size == (32, 32)

    # Error
    img_error = create_battery_icon(None, "error", False)
    assert img_error.size == (32, 32)

