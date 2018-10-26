"""
This little tool lets your search for and download books from libgen.io

Author:     Tyler Melton
Created:    10/25/2018
Modified:   10/25/2018
"""

"""
IMPORTS
"""

# Full package imports
import re
import urllib3

# Specific imports
from pprint import pprint
from bs4 import BeautifulSoup
from requests import Session


"""
MAIN
"""

url_ads = "http://download1.libgen.io/ads.php"

class LibgenSession(Session):
    def __init__(self):
        """
        LibgenSession extends the requests.Session class and adds
        methods for working specifically with libgen.io
        """

        # Run the Session init
        super().__init__()

        # Get config
        #self._config = LibgenConfig()

        # Headers in case the site checks UA
        self._header_cache_control = "no-cache"
        self._header_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        self._header_host = "libgen.io"
        self.headers.update({
            "User-Agent": self._header_ua,
            "Host": self._header_host,
            "Cache-Control": self._header_cache_control
        })

    def get_book(self, md5, out_dir):
        """
        Downloads the book

        :param md5: The md5 hash of the desired book
        :param filename: The output file (full path)
        :return:
        """

        # GET URL
        url = f"http://download1.libgen.io/ads.php?md5={md5}"

        # Make the request
        res = self.get(url)

        # Check return status
        if res.status_code != 200:
            raise Exception("Error retrieving file!")

        # Else, load up html
        dl_url = ""
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup.find_all("a"):
            if tag.string == "GET":
                dl_url = tag["href"]

        # Get filename from html
        filename = "outfile"
        tag = soup.find(id="textarea-example")
        if tag:
            filename = tag["value"]

        # Retrieve the book
        dl_res = self.get(dl_url)

        # Check return status
        if dl_res.status_code != 200:
            raise Exception("Failed open download URL!")

        # Download and save the book
        with open(f"{out_dir}/{filename}", "wb") as f:
            f.write(dl_res.content)

        # Success
        print("\nGot it!\n")
        print(f"\nSaved as: {filename}\n\n")

    def search_books(self, query):
        """
        Uses the libgen API to search for a given string.

        :param query: The string to search
        :return: A dictionary of names and md5 hashes
        """

        # Unencoded query string
        query_params = {
            "req": query,
            #"lg_topic": "libgen",
            #"open": "0",
            "view": "simple",
            "res": "100",
            "phrase": "1",
            "column": "def",
            "sort": "year",
            "sortmode": "DESC"
        }

        # Search
        search_url = "http://libgen.io/search.php"
        search_res = self.get(search_url, params=query_params)

        # Check return status
        if search_res.status_code != 200:
            pprint(f"\n\nStatus Code: {search_res.status_code}")
            pprint(f"\nReason: {search_res.reason}")
            pprint(f"\nRequest: {search_res.url}")
            pprint(f"\nContent: {search_res.content}\n\n")
            raise Exception("Failed to retrieve search results!")

        # Parse html
        soup = BeautifulSoup(search_res.text, "html.parser")

        # Get our target table
        tables = soup.findChildren("table")
        table = tables[2]

        # List of all books found
        books_found = []

        # For each useful row, create a LibgenBook
        rows = table.findChildren("tr")
        select_num = 1
        for i in range(2, len(rows)):

            # Grab the next table row and split into td array
            data = rows[i].findChildren("td")

            # Create a new book object
            book = LibgenBook()

            # Set the display number (for user selection)
            book.num = select_num
            select_num = select_num + 1

            # Set ID
            book.id = data[0].get_text()

            # Get authors
            for a in data[1].findChildren("a"):
               book.authors.append(a.get_text())

            # Get title
            book.title = data[2].get_text()

            # Get publisher
            book.publisher = data[3].get_text()

            # Get year
            book.year = data[4].get_text()

            # Get MD5
            for dr in data:
                for d in dr.findChildren("a"):
                    if "title" in d.attrs:
                        if d.attrs["title"] == "Libgen.io":
                            str = d.attrs["href"]

                            rx = re.compile(".*md5=(.*)")
                            m = rx.match(str)

                            book.md5 = m.group(1)
            books_found.append(book)

        # Return results
        return books_found


class LibgenBook:
    def __init__(self):
        """
        LibgenBook holds all the properties needed to download books
        from libgen.io
        """

        self.md5 = ""
        self.num = ""
        self.id = ""
        self.title = ""
        self.url = ""
        self.dl_url = ""
        self.authors = []
        self.publisher = ""
        self.year = ""

    def __str__(self):
        stri = f"({self.num}) => "
        stri = f"{stri}Title: {self.title}"
        stri = f"{stri} (Year: {self.year})\n"

        return stri


keep_going = True
while keep_going:

    # Create a new session
    s = LibgenSession()

    # Prompt user for search string
    qstr = ""
    qstr = input("Enter a search string: ")

    # Perform search
    if qstr == "":
        exit(0)
    books = s.search_books(qstr)

    # Display results
    for book in books:
        print(book)

    # Allow user to choose a book
    chosen = False
    choice = -1
    while not chosen:
        choice = int(input("Enter the number of the book you want: "))
        if 0 <= choice <= len(books):
            chosen = True

    # Get output directory
    outDir = ""
    while outDir == "":
        outDir = input("Enter the output directory: ")

    # Download the book
    s.get_book(books[choice].md5, outDir)

    keep_prompting = True
    while keep_prompting:
        # Run again?
        res = input("Search again (y/n)? ")

        if res == "n":
            keep_prompting = False
            keep_going = False
            print("\n\n")
        elif res == "y":
            keep_prompting = False
            keep_going = True
            print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")

# #s.get_book("C5FA82CB29E253ECD748D846A44FC620", "/Users/tylermelton/Desktop/")
# s.search_books("networking")
