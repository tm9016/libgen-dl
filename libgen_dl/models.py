"""
This file holds all of the data models and associated classes for
libgen_dl.

Author:     Tyler Melton
Created:    11/06/2018
Modified:   11/11/2018
"""

import uuid
from queue import Queue


class Book():
    """
    Book() holds all the properties needed to describe a book
    from libgen.io
    """

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.md5 = ""
        self.id = ""
        self.title = ""
        self.authors = []
        self.publisher = ""
        self.year = ""
        self.extension = ""

    def __str__(self):
        s = f"({self.id}) =>"
        s = f"{s} Title: {self.title}"
        s = f"{s} (Year: {self.year})"
        s = f"{s} (EXT: {self.extension})"

        return s


class ResultSet:
    """
    Holds a set of search results from libgen.io, including
    pagination information
    """

    def __init__(self):

        # List of books found
        self.results = []

    def add(self, book):
        """
        Add a book to the results set

        :param book: A libgen_dl Book to add
        :return:
        """

        self.results.append(book)

    def reset(self):
        """
        Clear the results list

        :return:
        """

        self.results = []


class DownloadQueue(Queue):
    """
    A queue for holding a list of books for download.

    *** Currently, this is just a wrapper for python's Queue ***
    """

    def __init__(self):
        super().__init__()
