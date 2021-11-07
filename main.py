import base64
import streamlit as st
import gen_wallpaper
import pandas as pd
import numpy as np
import json
import os
st.set_option("deprecation.showfileUploaderEncoding", False)

st.markdown("""
# Alchemy Stars Wallpaper Generator

Create  wallpapers for your favourite Alchemy Stars operators!

Use the download link at the bottom for the best image quality!

You can find the app code on GitHub [here](https://github.com/Ze1598/alchemy-stars-wallpapers).

The app was coded by [@Ze1598](https://github.com/Ze1598), and tested and designed by [@MiguelACAlmeida](https://github.com/MiguelACAlmeida).
""")


def load_data() -> pd.DataFrame:
    csv_path = os.path.join(os.getcwd(), "static", "data", "data.csv")
    data = pd.read_csv(csv_path)
    # Sort DF by operator name
    data.sort_values(
        ["Name"], 
        axis="rows",
        ascending=True, 
        inplace=True
    )
    return data


def encode_img_to_b64(img_name: str) -> bytes:
    """Given the name of a image file, load it in bytes mode, and convert it to a base 64 bytes object.
    """
    # https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806/19
    with open(img_name, "rb") as f:
        img = f.read()
        encoded_img = base64.b64encode(img).decode()

    return encoded_img


# Load the main DF with all art data
main_data = load_data()

# Dropdown to filter by operator rarity
char_rarity = st.selectbox(
    "Choose the operator rarity",
    ("6-star", "5-star", "4-star", "3-star")
)

# Get a subset DF for the filtered rarity
operator_rank_int = int(char_rarity[0])
filtered_data = main_data.query(f"Rarity == {operator_rank_int}")

# Dropdown to choose the character
char_chosen = st.selectbox(
    "Choose your character",
    np.unique(filtered_data["Name"].to_numpy())
)
# Filter for this character
filtered_data = main_data.query(f"Name == '{char_chosen}'")


# Dropdown to choose character art
# List of skin names
skins_available = filtered_data.dropna(subset=["SkinUrl"])["Skin"].to_numpy().tolist()
# Has Asc. 3 if they have an Asc. 3 art URL
has_ascension_3 = np.unique(
    filtered_data.dropna(subset=["Ascension3"])["Ascension3"].to_numpy()
).shape != (0,)
# Art choices are the ascensions and the skins
art_choices = ["Ascension 0"] + (["Ascension 3"] if has_ascension_3 else list()) + skins_available
art_chosen = st.selectbox(
    "Choose the character art",
    art_choices
)

# Get the row of data as a dict, but conditionally for characters with multiple skins
if art_chosen.startswith("Skin"):
    char_info = filtered_data.query(f"Skin == '{art_chosen}'").to_dict("records")[0]
else:
    char_info = filtered_data.to_dict("records")[0]

chosen_colour = st.color_picker("Optionally change the background colour", char_info["BaseColour"])

char_align = st.selectbox(
    "How do you want to align the character?",
    ["Right", "Left", "Centred"]
)

render_faction = st.checkbox("Include character's faction logo?")

# Build a new dictionary with the specific info to generate the wallpaper
art_url = char_info["SkinUrl"] if art_chosen.startswith("Skin") \
    else char_info["Ascension0"] if art_chosen == "Ascension 0" \
    else char_info["Ascension3"]
art_info = {
    "Name": char_info["Name"],
    "Url": art_url,
    "Colour": chosen_colour,
    "FactionLogo": char_info["FactionLogo"],
    "RenderFaction": render_faction,
    "BaseColour": char_info["BaseColour"],
    "CharAlign": char_align
}
wallpaper_name = gen_wallpaper.wallpaper_gen(art_info)

# Display the image on the page
st.image(
    wallpaper_name, 
    width=None, 
    use_column_width="auto",
    caption="Wallpaper preview"
)

# Encode the image to bytes so a download link can be created
encoded_img = encode_img_to_b64(wallpaper_name)
href = f'<a href="data:image/png;base64,{encoded_img}" download="{wallpaper_name}">Download the graphic</a>'
# Create the download link
st.markdown(href, unsafe_allow_html=True)

# Delete the graphic from the server
os.remove(wallpaper_name)
try:
    os.remove(wallpaper_name)
except:
    pass