# alchemy-stars-wallpapers
[live app](https://alchemy-stars-wallpapers.herokuapp.com/)

A web app built with [Streamlit](https://www.streamlit.io/) in Python to create Alchemy Stars desktop wallpapers on the fly.

The app was coded by [@Ze1598](https://github.com/Ze1598), and tested and designed by [@MiguelACAlmeida](https://github.com/MiguelACAlmeida).

The art was scraped from the [Wikia](https://alchemystars.fandom.com/wiki/Category:Characters) and images are loaded directly from their source. This scraping is done with with the [requests](https://pypi.org/project/requests/) and [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) libraries.
The background colours are chosen dynamically by analysing the art and detecting the most dominant colour.