from requests_html import HTMLSession


class ParserGr:
    def __init__(self, isbn):
        try:
            self.isbn = isbn
            self.link = ('https://www.goodreads.com/search?q=' + isbn + '&qid=')
            session = HTMLSession()
            r = session.get(self.link)
            info = r.html.find('div.leftContainer', first=True)
            book = info.find('div.uitext.stacked', first=True)
            spans = book.find('span')
            self.rating_gr = spans[6].text

        except Exception as e:
            print(f"GoodReads parsing failed: {e}")
            self.rating_gr = "Error"
