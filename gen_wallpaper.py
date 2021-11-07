from PIL import Image, ImageFilter, ImageEnhance
from colorthief import ColorThief
import requests
from io import BytesIO
from typing import List, Tuple, Dict
from requests.models import Response
import pandas as pd
import os


def get_colour_palette(res: Response) -> List[Tuple[int]]:
    # Load the image as binary data (contents of the request's response)
    img_bytes = BytesIO(res.content)

    colour_thief = ColorThief(img_bytes)
    # Build a colour palette
    palette = colour_thief.get_palette(color_count=6)

    return palette


def prepare_char_art(url: str) -> any:
    res = requests.get(url)
    char_art = Image\
        .open(BytesIO(res.content), mode="r")\
        .convert("RGBA")#\
        # .resize((1382, 1382))
    return char_art


def prepare_faction_art(url: str) -> any:
    res = requests.get(url)
    faction_art = Image\
        .open(BytesIO(res.content), mode="r")\
        .convert("RGBA")

    ratio = 1
    size = faction_art.size
    new_size = [int(s * ratio) for s in size]
    faction_art = faction_art.resize(new_size)

    # Get the alpha channel
    alpha = faction_art.getchannel("A")
    # Adjust the brightness of the alpha channel to the desired opacity level
    alpha = ImageEnhance.Brightness(alpha).enhance(0.2)
    # Instead of changing the image's alpha channel value, update it with\
    # an already transformed image channel
    faction_art.putalpha(alpha)
    return faction_art


def increment_colour(colour: str, update_delta: float) -> str:
    """Increment the most saturated RGB channel of the operator color to create the footer block color.
    If more than one channels have the most saturation, then those are all updated.
    """
    # Get the individual RGB channels
    channels = [
        int(colour[1:3], 16),
        int(colour[3:5], 16),
        int(colour[5:], 16)
    ]
    # String to hold the final color
    new_color = "0x"
    # Loop through the color channels to update the most saturated one(s),\
    # adding the result to the running string
    for channel in channels:
        # Only update the channel if it is (one of) the most saturated and\
        # it is not already at max saturation
        if (max(channels) == channel) and (channel != 255):
            updated_channel = int(channel * (1+update_delta))
            # Clip the saturation to the maximum value possible
            if updated_channel > 255:
                updated_channel = 255
            # Don't add the initial "0x" characters to the string
            hex_channel = hex(updated_channel)[2:]
            new_color += hex_channel
        # Otherwise, add the color as is
        else:
            hex_conv = hex(channel)[2:]
            # In case the channel add a leading 0, make sure it is kept
            if len(hex_conv) == 1:
                hex_conv = "0" + hex_conv
            new_color += hex_conv

    # If the resulting hexadecimal is still a valid hex color (i.e., a\
    # positive hex value), use it, otherwise the new color will simply be black
    if int(new_color, 16) < int("0x000", 16):
        new_color = "0xFFF"
    # Replace Python's "0x" notation with a proper pound symbol
    new_color = new_color.replace("0x", "#")
    return new_color


def complement_hex(hex_colour: str) -> str:
    result = "#"
    for i in range(1, 7, 2):
        # Get channel values
        channel = hex_colour[i:i+2]
        # Convert to decimal from hex
        channel = int(channel, 16)
        # Get complement
        result_rgb = 255 - channel
        # Back to hex
        result_hex = hex(result_rgb)
        # Without the 0x
        result += result_hex[2:]

    return result


def get_adapted_art_coords(alignment: str, art_dim: Tuple, wallpaper_dim: Tuple, og_coord: Tuple) -> Tuple:
    art_width, art_height = art_dim[0], art_dim[1]
    if alignment == "Right":
        # Basically ensure images thinner than half the wallpaper's width are rendered on the right
        if art_width < 800:
            art_x = int( (wallpaper_dim[0] // 4) * 2.5 )
        elif art_width < 1300:
            art_x = int( (wallpaper_dim[0] // 4) * 2 )
        elif art_width < (wallpaper_dim[0] // 2):
            art_x = (wallpaper_dim[0] // 4) * 3
        else:
            art_x = og_coord[0]

    if alignment == "Left":
        # Same as above, but on left side
        if art_width < 800:
            art_x = 0
        elif art_width < 1300:
            art_x = -150
        elif art_width > 1700:
            art_x = -700
        elif art_width < (wallpaper_dim[0] // 2):
            art_x = int( (wallpaper_dim[0] // 4) )
        else:
            art_x = -og_coord[0]

    if alignment == "Centred":
        # Center-aligned, that's it
        art_x = (wallpaper_dim[0] - art_dim[0]) // 2

    # And short images are rendered with a positive coordinate
    if art_height < wallpaper_dim[1]:
        art_y = 75
    elif art_height < 1300:
        art_y = 0
    elif art_height > 1500:
        art_y = -200
    else:
        art_y = og_coord[1]

    return (art_x, art_y)


def wallpaper_gen(art_info: Dict) -> str:
    WALLPAPER_DIM = (1920, 1080)
    ART_COORD = (500, -100)
    FACTION_COORD = (-200, -75)
    FACTION_COORD = (0, 15)

    # Set up the file name and save path
    wallpaper_name = f"{art_info['Name']}.png"
    wallpaper_path = os.path.join(os.getcwd(), wallpaper_name)

    # Request the operator art
    char_art = prepare_char_art(art_info["Url"])
    faction_art = prepare_faction_art(art_info["FactionLogo"])

    # Update left coordinate to draw character art based on the art dimensions
    ART_COORD = get_adapted_art_coords(art_info["CharAlign"], char_art.size, WALLPAPER_DIM, ART_COORD)

    # Create a new image
    # bg_colour = complement_hex(art_info["Colour"])
    # bg_colour = increment_colour(bg_colour, 0.25)
    wallpaper = Image.new("RGBA", WALLPAPER_DIM, color=art_info["Colour"])
    # wallpaper = Image.new("RGBA", (1920, 1080), color = bg_colour)

    # Generate coloured shadows for a nice effect
    SHADOW_OFFSET = (10, 10)
    SHADOW_COORD = tuple(ART_COORD[i] + SHADOW_OFFSET[i] for i in range(len(ART_COORD)))
    SHADOW_COORD_2 = tuple(SHADOW_COORD[i] + SHADOW_OFFSET[i] for i in range(len(SHADOW_COORD)))

    shadow_colour = increment_colour(art_info["BaseColour"], 0.6)
    shadow = Image.new("RGBA", char_art.size, color=shadow_colour)
    wallpaper.paste(shadow, SHADOW_COORD_2, mask=char_art)

    shadow_colour = increment_colour(shadow_colour, 0.35)
    shadow = Image.new("RGBA", char_art.size, color=shadow_colour)
    wallpaper.paste(shadow, SHADOW_COORD, mask=char_art)

    # Blur just the shadows before adding the art itself
    wallpaper = wallpaper.filter(ImageFilter.BoxBlur(10))

    # Paste in the faction logo
    if art_info["RenderFaction"]:
        wallpaper.paste(faction_art, FACTION_COORD, mask=faction_art)
    
    # Now paste the actual operator art
    wallpaper.paste(char_art, ART_COORD, mask=char_art)

    # Finally save the result
    wallpaper.save(wallpaper_path)

    return wallpaper_name


if __name__ == "__main__":
    pass