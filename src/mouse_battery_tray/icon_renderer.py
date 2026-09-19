import os

from PIL import Image, ImageDraw, ImageFont


def create_battery_icon(percentage, status, is_charging=False, low_battery_threshold=20):
    """
    Creates a 32x32 icon with a large number or symbol.
    
    Args:
        percentage: Battery percentage (int or None)
        status: one of 'connected', 'disconnected', 'device_not_found', 'error'
        is_charging: bool
        low_battery_threshold: int
    """
    # Create a 32x32 image with full transparency
    image = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Determine background color and text
    bg_color = (0, 0, 0, 255)  # Pure black for contrast
    text = "--"
    text_color = (255, 255, 255, 255) # White

    if status == "connected":
        if percentage is not None:
            if percentage >= 100:
                text = "99+"
            else:
                text = str(percentage)
            
            if is_charging:
                bg_color = (0, 150, 0, 255) # Clear Green
            elif percentage <= low_battery_threshold:
                bg_color = (220, 0, 0, 255) # Bright Red
            else:
                bg_color = (30, 30, 30, 255) # Dark Gray for normal
        else:
            text = "--"
            bg_color = (60, 60, 60, 255)
    elif status == "disconnected" or status == "device_not_found":
        text = "--"
        bg_color = (60, 60, 60, 255)
    else: # error
        text = "!"
        bg_color = (200, 80, 0, 255) # Orange

    # Draw rounded rectangle background - maximized size (0,0 to 31,31)
    # Use a small radius to keep it looking like a tray icon but maximize area
    draw.rounded_rectangle([0, 0, 31, 31], radius=4, fill=bg_color)

    # Load font
    try:
        # Use Arial Bold for maximum thickness
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

    # Center text accurately
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        # Center horizontally, and adjust vertically (h in bbox is often baseline-based)
        x = (32 - w) // 2
        # Optical adjustment for centering capital letters/numbers
        y = (32 - h) // 2 - 3
        
        draw.text((x, y), text, fill=text_color, font=font)
    except AttributeError:
        # Fallback
        draw.text((4, 4), text, fill=text_color, font=font)

    return image

