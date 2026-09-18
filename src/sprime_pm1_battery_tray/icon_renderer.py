from PIL import Image, ImageDraw, ImageFont
import os


def create_battery_icon(percentage, status, is_charging=False, low_battery_threshold=20):
    """Create a 32x32 tray icon with a large battery number or state symbol."""
    image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    bg_color = (0, 0, 0, 255)
    text = "--"
    text_color = (255, 255, 255, 255)

    if status == "connected":
        if percentage is not None:
            text = "99+" if percentage >= 100 else str(percentage)
            if is_charging:
                bg_color = (0, 150, 0, 255)
            elif percentage <= low_battery_threshold:
                bg_color = (220, 0, 0, 255)
            else:
                bg_color = (30, 30, 30, 255)
        else:
            text = "--"
            bg_color = (0, 150, 0, 255) if is_charging else (60, 60, 60, 255)
    elif status in {"disconnected", "device_not_found"}:
        text = "--"
        bg_color = (60, 60, 60, 255)
    else:
        text = "!"
        bg_color = (200, 80, 0, 255)

    draw.rounded_rectangle([0, 0, 31, 31], radius=4, fill=bg_color)

    try:
        font_path = "C:\\Windows\\Fonts\\arialbd.ttf"
        if not os.path.exists(font_path):
            font_path = "arial.ttf"
        if text == "99+":
            font = ImageFont.truetype(font_path, 15)
        elif len(text) >= 2:
            font = ImageFont.truetype(font_path, 23)
        else:
            font = ImageFont.truetype(font_path, 26)
    except OSError:
        font = ImageFont.load_default()

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x = (32 - width) // 2
        y = (32 - height) // 2 - 3
        draw.text((x, y), text, fill=text_color, font=font)
    except AttributeError:
        draw.text((4, 4), text, fill=text_color, font=font)

    return image
