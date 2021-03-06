#! /usr/bin/env python3
"""
This little tool lets your search for and download books from libgen.io

Author:     Tyler Melton
Created:    10/25/2018
Modified:   11/04/2018
"""

# Full package imports
import re
import os
import sys
import time
import threading

# Specific imports
from pprint import pprint
from bs4 import BeautifulSoup
from requests import Session
from queue import Queue


"""
Classes
"""


class LibgenSession(Session):
    def __init__(self):
        """
        LibgenSession extends the requests.Session class and adds
        methods for working specifically with libgen.io
        """

        # Run the Session init
        super().__init__()

        # Headers in case the site checks UA
        self._header_cache_control = "no-cache"
        self._header_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        self._header_host = "libgen.io"
        self.headers.update({
            "User-Agent": self._header_ua,
            "Host": self._header_host,
            "Cache-Control": self._header_cache_control
        })

    def get_book(self, md5, out_dir, filename=""):
        """
        Downloads the book

        :param md5: The md5 hash of the desired book
        :param filename: (Optional) The output file name
        :param out_dir: The output directory
        :return:
        """

        # GET URL
        ads_url = f"http://libgen.io/ads.php?md5={md5}"

        # Make the request
        ads_res = self.get(ads_url)

        # Check return status
        if ads_res.status_code != 200:
            raise Exception("Error retrieving key!")

        # Else, load up html
        dl_url = ""
        soup = BeautifulSoup(ads_res.text, "html.parser")
        for tag in soup.find_all("a"):
            if tag.string == "GET":
                dl_url = tag["href"]

        # Retrieve the book
        dl_res = self.get(dl_url)

        # Get filename from response header if available
        fn_hdr = dl_res.headers.get("Content-Disposition")
        if isinstance(fn_hdr, str):
            fn_re = re.compile(r".*filename=\"(.*\..*)\"$")
            fn_m = fn_re.match(fn_hdr)
            if len(fn_m.groups()) > 0:
                filename = fn_m.group(1)

        # Check return status
        if dl_res.status_code != 200:
            raise Exception("Failed open download URL!")

        # Download and save the book
        with open(f"{out_dir}/{filename}", "wb") as f:
            f.write(dl_res.content)

        # Success
        print("\nGot it!\n")
        print(f"\nSaved as: {filename}\n\n")

    def get_search_params(self, query):
        """
        Builds a dictionary of search parameters with default
        values and the provided search query.

        :param query: The search query
        :return: A dictionary of parameters to provide to requests
        """

        return {
            "req": query,
            "lg_topic": "libgen",
            # "open": "0",
            "view": "simple",
            "res": "100",
            "phrase": "1",
            "column": "def",
            "sort": "year",
            "sortmode": "DESC"
        }

    def get_search_result(self, url, params):
        """
        Performs a search on libgen.io and returns the
        HTTP response. Validates the response before
        returning.

        :param url: The search url
        :param params: The search parameters (a dictionary)
        :return: HTTP response object
        """

        # Run the search
        res = self.get(url=url, params=params)

        # Check return status
        if res.status_code != 200:
            pprint(f"\n\nStatus Code: {res.status_code}")
            pprint(f"\nReason: {res.reason}")
            pprint(f"\nRequest: {res.url}")
            pprint(f"\nContent: {res.content}\n\n")
            raise Exception("Failed to retrieve search results!")

        return res

    def search_books(self, query):
        """
        Uses the libgen API to search for a given string.

        :param query: The string to search
        :return: A dictionary of names and md5 hashes
        """

        # Get params and run search
        search_params = self.get_search_params(query)
        search_url = "http://libgen.io/search.php"
        search_res = self.get_search_result(search_url, search_params)

        # Parse html
        soup = BeautifulSoup(search_res.text, "html.parser")

        # Get our target table
        tables = soup.findChildren("table")
        table = tables[2]

        # List of all books found
        books_found = []

        # For each useful row, create a LibgenBook
        rows = table.findChildren("tr")

        # Get the column headers and their positions
        header_row = rows[0].findChildren('td')
        key_offsets = {}
        for i in range(len(header_row)):
            if header_row[i].string == "ID":
                key_offsets.update({"id": i})
            elif header_row[i].string == "Author(s)":
                key_offsets.update({"authors": i})
            elif header_row[i].string == "Title":
                key_offsets.update({"title": i})
            elif header_row[i].string == "Publisher":
                key_offsets.update({"publisher": i})
            elif header_row[i].string == "Year":
                key_offsets.update({"year": i})
            elif header_row[i].string == "Pages":
                key_offsets.update({"pages": i})
            elif header_row[i].string == "Language":
                key_offsets.update({"language": i})
            elif header_row[i].string == "Size":
                key_offsets.update({"size": i})
            elif header_row[i].string == "Extension":
                key_offsets.update({"extension": i})
            else:
                continue

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
            book.id = data[key_offsets["id"]].string

            # Get authors
            for a in data[key_offsets["authors"]].findChildren("a"):
                book.authors.append(a.string)

            # Get title
            book.title = data[key_offsets["title"]].get_text()

            # Get publisher
            book.publisher = data[key_offsets["publisher"]].string

            # Get year
            book.year = data[key_offsets["year"]].string

            # Get extension
            book.extension = data[key_offsets["extension"]].string

            # Get MD5
            for i in range(key_offsets["extension"]+1, len(data)):
                md5_td = data[i]
                md5_links = md5_td.findChildren("a")
                for link in md5_links:
                    if "title" in link.attrs and link.attrs["title"] == "Libgen.io":
                        md5_str = link.attrs["href"]
                        md5_re = re.compile(r".*md5=(.*)")
                        md5_m = md5_re.match(md5_str)
                        book.md5 = md5_m.group(1)

            # Add book to the list
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
        self.extension = ""
        self.url_ads = ""
        self.url_dl = ""

    def __str__(self):
        s = f"({self.num}) => "
        s = f"{s}Title: {self.title}"
        s = f"{s} (Year: {self.year})"
        s = f"{s} (EXT: {self.extension})"

        return s


"""
Main
"""


def prompt_user():
    """
    Ask the user whether or not to end the script.
    """

    keep_prompting = True
    while keep_prompting:
        # Run again?
        res = input("Search again (y/n)? ")

        if res == "n":
            keep_prompting = False
            print("\n\n")
            return False
        elif res == "y":
            keep_prompting = False
            print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
            return True


def get_search():
    """
    Prompt the user for a search term. Handle edge cases.
    """

    # Min search length
    MIN_STR_LEN = 3

    # Keep asking until a satisfactory answer is provided. Ctrl-C to
    # cancel and exit (for now).
    while True:
        s_str = input("Enter a search string: ")

        # If string is too short, fail and ask again
        if len(s_str) < MIN_STR_LEN:
            err_str = f"\nSearch string too short! Must be"
            err_str = f"{err_str} {MIN_STR_LEN} characters or less.\n"
            print(err_str)
        else:
            return s_str


def get_book_selection(books):
    """
    Show the user a list of books and ask for a selection.
    """

    # Display the books
    for book in books:
        print(book)

    # Allow user to choose a book
    chosen = False
    while not chosen:
        choices = [int(x) for x in (input("Enter the number of the book you want: ").split())]
        for c in choices:
            if 1 <= c <= len(books):
                chosen = True

    return choices


def worker_download(q, session, out_dir):
    """
    A worker that runs a single download. This is to be run alongside
    other worker_download()'s in multiple threads.
    """

    # Get next book
    b = q.get()

    # Download
    filename = f"{b.title}.{b.extension}"
    session.get_book(b.md5, out_dir, filename)

    # End
    q.task_done()
    sys.exit()


def run_threads():
    """
    Main loop. Allows the user to search for books and download them
    in sets. Uses threads to keep the max concurrent downloads
    running.
    """

    # Default output directory
    DEFAULT_OUT_DIR = f"{os.environ.get('HOME')}/Desktop"

    # Maximum concurrent downloads
    MAX_CONC_DLS = 3

    # Set up a new session
    s = LibgenSession()

    # Get the search string
    s_str = get_search()

    # Search for the given string and store the books in memory
    books = s.search_books(s_str)

    # Get book choices
    choices = get_book_selection(books)

    # Get output directory
    out_dir = input("Enter the output directory: ")
    if out_dir == "":
        out_dir = DEFAULT_OUT_DIR
        print(f"\nNo output directory provided! Using {out_dir}...")

    # Queue to hold books for download
    q = Queue()

    # Populate queue and create threads
    dl_threads = []
    for c in choices:
        b = books[c-1]
        q.put(b)
        t = threading.Thread(target=worker_download, args=(q, s, out_dir))
        dl_threads.append(t)

    # Run threads, three at a time
    index = 0
    while not q.empty():
        if threading.active_count() <= MAX_CONC_DLS:
            dl_threads[index].start()
            index += 1
        time.sleep(3)

    active_threads = threading.active_count()
    while active_threads > 1:
        time.sleep(1)
        active_threads = threading.active_count()

    if prompt_user():
        run_threads()


def run():

    # Default output directory
    DEFAULT_OUT_DIR = f"{os.environ.get('HOME')}/Desktop"

    keep_going = True
    while keep_going:

        # Create a new session
        s = LibgenSession()

        # Prompt user for search string
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
            choice = [int(x) for x in (input("Enter the number of the book you want: ").split())]
            for c in choice:
                if 1 <= c <= len(books):
                    chosen = True

        # Get output directory
        out_dir = input("Enter the output directory: ")
        if out_dir == "":
            out_dir = DEFAULT_OUT_DIR
            print(f"\nNo output directory provided! Using {out_dir}...")

        # Download the book
        for c in choice:
            b = books[c-1]
            fn = f"{b.title}.{b.extension}"
            s.get_book(b.md5, out_dir, fn)

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


# Allow standalone execution
if __name__ == "__main__":
    run_threads()