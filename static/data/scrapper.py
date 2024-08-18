from io import BytesIO
from bs4 import BeautifulSoup
import requests
import pickle
import json
import datetime
import pandas as pd
from typing import Dict, SupportsBytes, Tuple
from colorthief import ColorThief
import logging
logging.basicConfig(level=logging.INFO)


def get_characters() -> Dict:
    """Generate a dictionary to map character names to the URL of their pages.

    Returns:
        Dict[str]: the dictionary of characters and their page URL.
    """
    logging.info(f"{datetime.datetime.now()}: Scraping character pages")

    # Load the pickle file with the operator pages
    with open("char_pages.pickle", "rb") as f:
        pickle_data = pickle.load(f)

    # GET the HTML from the page of characters
    chars_url = "https://alchemystars.fandom.com/wiki/Category:Characters"
    # Alternate source (at least gets updated quicker)
    chars_url = "https://alchemystars.fandom.com/wiki/Category:Characters?from=%C2%A1"
    req = requests.get(chars_url)
    soup = BeautifulSoup(req.content, "lxml")

    # There"s an <a> with the character name and page url
    chars = soup.find_all("a", class_="category-page__member-link")

    if len(chars) != len(pickle_data.keys()):
        logging.info(
            f"{datetime.datetime.now()}: Pickle data out of date - scraping anew")
        # Get just names
        char_names = [char.text for char in chars]
        # Get just page urls
        char_pages = [f"{BASE_URL}{char['href']}" for char in chars]
        # Map character name to their page url
        char_dict = {char: page_url for char,
            page_url in zip(char_names, char_pages)}
    else:
        logging.info(f"{datetime.datetime.now()}: Pickle data up to date")
        char_dict = pickle_data

    with open("char_pages.pickle", "wb") as f:
        pickle.dump(char_dict, f)

    return char_dict


def get_single_char_info(page_url: str) -> Dict:
    """Get all the information for a single character: URL to images (ascension and skins), rarity, and elements.

    Args:
        page_url (str): URL to the character page

    Returns:
        Dict: Dictionary with all information: Ascension0 and Ascension3 art URLs (if they exist), elements, rarity and skins (one key per skin)
    """
    # GET the HTML for the character page
    req = requests.get(page_url)
    soup = BeautifulSoup(req.content, "lxml")

    # Use the character rarity to check if the page belongs to a playable character
    try:
        # Rarity is derived from the second class of the element with the rarity icons
        char_rarity = soup.find(
            "div", 
            class_="rarity_star"
        )["class"][1].replace("star", "")
    except:
        return dict()

    # Main and Sub elements can be derived from the element images" alt attributes
    main_element = soup.find("div", class_="aurorian_element1").find("img")[
                             "alt"].split(" ")[1].split(".")[0]
    sub_element = soup.find("div", class_="aurorian_element2")
    # Subelement might not exist so only finish scraping if it does exist
    if sub_element != None:
        sub_element = sub_element.find("img")["alt"].split(" ")[1].split(".")[0]

    # Artwork is scraped from the gallery tab
    req = requests.get(page_url + "/Gallery")
    soup = BeautifulSoup(req.content, "lxml")

    # Faction image is available in the first tab
    try:
        generic_images = soup.find(id="gallery-0").find_all("div", class_="wikia-gallery-item")
    except:
        return dict()
    faction_image = filter(lambda div: "Character Logo" in div.text, generic_images)
    faction_image = next(faction_image).find("img")["src"].split(".png")[0] + ".png" 
 
    # Find the div for the base artwork    
    artworks = soup.find(id="gallery-1").find_all("div", class_="wikia-gallery-item")
 
    # Extract the artwork URL (original size)
    ascension_zero = filter(lambda div: "Base" in div.text, artworks)
    ascension_zero = next(ascension_zero).find("img")["src"].split(".png")[0] + ".png" 
    
    # Find the div for the A3 artwork
    ascension_three = filter(lambda div: "Ascension" in div.text, artworks)
    # Check that A3 exists, if not url is set to None
    _list = list(ascension_three)
    if _list != list():
        # Then extract the artwork URL (original size)
        ascension_three = _list[0].find("img")["src"].split(".png")[0] + ".png"
    else:
        ascension_three = None
    
    # Skins are all other artwork
    skins = filter(lambda div: div.text not in ("Base", "Ascension 3", "Equipment"), artworks)
    _list = list(skins)
    skin_dict = {
        f"Skin{skin_num}": div.find("img")["src"].split(".png")[0] + ".png"
         for skin_num, div in zip( range(1, len(_list) + 1), _list )
    }
    
    return {
        "Ascension0": ascension_zero,
        "Ascension3": ascension_three,
        # Bring the skins as individual keys
        **skin_dict,
        "Element": main_element,
        "SubElement": sub_element,
        "Rarity": char_rarity,
        "FactionLogo": faction_image if faction_image else None
    }    


def gen_operator_colour(art_url: str) -> str:
    """Generate a colour for an operator by detecting the most dominant colour on their E0 art.

    Args:
        art_url (str): URL to the Ascension artwork to use as source.

    Returns:
        str: Generated colour (hexadecimal).
    """
    # Request the image
    img_req = requests.get(art_url)
    # Read the response content
    img_bytes = BytesIO(img_req.content)
    # Create a ColorThief object for the image (in bytes)
    colour_thief = ColorThief(img_bytes)
    # Build a colour palette
    palette = colour_thief.get_palette(color_count=2)
    # Convert the generated colour to hex
    colour_chosen = palette[0]
    colour_chosen = f"#{colour_chosen[0]:02x}{colour_chosen[1]:02x}{colour_chosen[2]:02x}"
    # Return only the most dominant colour
    return colour_chosen


def main():
    # Dict of characters and their page URL
    char_dict = get_characters()
    
    # List of dictionaries to hold information for each character
    data = list()
    # Scrape all information for each character
    for char in char_dict:
        # if char in ["Victoria", "Nemesis", "Vice", "Paloma"]:
        logging.info(f"{datetime.datetime.now()}: Scraping {char}")

        char_info = get_single_char_info(char_dict[char])

        # Mechanism to filter out non-playable characters
        if char_info == dict(): 
            logging.info(f"{datetime.datetime.now()}: {char} is not a playable character or is missing character art")
            continue
        # Just the Skin keys
        skins = {key: char_info[key] for key in char_info if key.startswith("Skin")}
        single_char = {
            "Name": char,
            "Rarity": char_info["Rarity"],
            "Element": char_info["Element"],
            "SubElement": char_info["SubElement"],
            "Ascension0": char_info["Ascension0"],
            "Ascension3": char_info["Ascension3"],
            "FactionLogo": char_info["FactionLogo"],
            # The skin keys will be columns in the dataframe
            **skins
        }
        # Generate the character colour based on their Asc. 3 art if it exists, else Asc. 0
        img_for_colour_gen = single_char["Ascension3"] if single_char["Ascension3"] != None else single_char["Ascension0"]
        single_char["BaseColour"] = gen_operator_colour(img_for_colour_gen)
        # Append the complete dictionary to the running list of dictionaries
        data.append(single_char)
        
    logging.info(f"{datetime.datetime.now()}: Scraped {len(data)} characters")

    # Let pandas infer the columns from what is in the dictionaries of the list
    df = pd.DataFrame(data)
    # But unpivot the skin columns, so there"s one with the skin number and another with its URL
    id_cols = [col for col in df.columns if not col.startswith("Skin")]
    skin_columns = [col for col in df.columns if col.startswith("Skin")]
    df = df.melt(
        id_vars = id_cols, 
        value_vars = skin_columns,
        var_name = "Skin", 
        value_name = "SkinUrl"
    )
    # Based on the Name and SkinUrl, drop duplicates of this pair, i.e.,
    # characters without skins have only a single row
    df = df.drop_duplicates(
        subset = ["Name", "SkinUrl"],
        keep = "first"
    )
    # Drop rows for skins without URL, except for Skin1 rows (even if a
    # character doesn"t have skins, they will have this row with empty SkinUrl)
    df = df[ 
        ( (df["SkinUrl"].notnull()) & (df["Skin"] != "Skin1") )
        | (df["Skin"] == "Skin1") 
    ]
    df.to_csv("data.csv", index=False)
    logging.info(f"{datetime.datetime.now()}: Exported data as CSV")


if __name__ == "__main__":
    BASE_URL = "https://alchemystars.fandom.com"
    main()
