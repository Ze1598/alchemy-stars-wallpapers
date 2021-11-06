from io import BytesIO
from bs4 import BeautifulSoup
import requests
import pickle
import json
import datetime
import pandas as pd
from typing import Dict, Tuple
from colorthief import ColorThief
import logging
logging.basicConfig(level=logging.INFO)

BASE_URL = "https://alchemystars.fandom.com/"

def get_characters() -> Dict:
    """Generate a dictionary to map character names to the URL of their pages.

    Returns:
        Dict[str]: the dictionary of characters and their page URL.
    """
    # GET the HTML from the page of characters
    chars_url = "https://alchemystars.fandom.com/wiki/Category:Characters"
    req = requests.get(chars_url)
    soup = BeautifulSoup(req.content, "lxml")

    # There's an <a> with the character name and page url
    chars = soup.find_all("a", class_="category-page__member-link")
    # Get just names
    char_names = [char.text for char in chars]
    # Get just page urls
    char_pages = [f"{BASE_URL}{char['href']}" for char in chars]
    # Map character name to their page url
    char_dict = {char: page_url for char, page_url in zip(char_names, char_pages)}

    # chars_df = pd.DataFrame({
    #     "Name": char_names,
    #     "PageUrl": char_pages,
    #     "AscensionZeroImage": asc_zero_urls,
    #     "AscensionThreeImage": asc_three_urls
    # })
    return char_dict

def get_single_char_info(page_url: str) -> Tuple[str]:
    # GET the HTML for the character page
    req = requests.get(page_url)
    soup = BeautifulSoup(req.content, "lxml")

    stages = ["Base", "Ascension 3"]
    stage_names = ["AscensionZero", "AscensionThree"]
    thumbnail_elems = soup.find_all("img", class_="pi-image-thumbnail")
    # Just the relevant ones
    thumbnail_elems = [img["src"] for img in thumbnail_elems if img["alt"] in stages]
    img_dict = {
        name: img.split("/revision")[0] for name, img in zip(stage_names, thumbnail_elems)
    }
    print(img_dict)
    




if __name__ == "__main__":
    char_dict = get_characters()
    for char in char_dict:
        get_single_char_info(char_dict[char])
        break