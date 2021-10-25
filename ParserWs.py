from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup


class ParserWs:
    def __init__(self, isbn):
        try:
            self.isbn = isbn
            self.link = ('https://www.waterstones.com/books/search/term/' + isbn)
            session = HTMLSession()
            r = session.get(self.link)
            info = r.html.find('div.price', first=True)
            price_new_uncut = info.find('b', first=True).text
            self.price_new = price_new_uncut.replace(" ", "")

        except Exception as e:
            print(f"Waterstones parsing failed: {e}")
            self.price_new = "Error"
            self.link = "Error"
            self.picture = "Error"
