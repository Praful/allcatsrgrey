import os
import sys
from bs4 import BeautifulSoup
import csv
import contextlib
import io
import re
import requests

TAB = '\t'

def is_blank(s):
    return not (s and s.strip())

def to_hex(s):
    return s.encode("utf-8").hex()

#  replchars = re.compile(r'[\n\r]')
replchars = re.compile(r'[\x00-\x1f]') 
def replchars_to_hex(match):
    return r'\x{0:02x}'.format(ord(match.group()))

def ctrl_chars(s):
    return replchars.sub(replchars_to_hex, s)

def clean_string(s):
    if s:
        return s.strip(" :\r\xa0")
    else:
        return s

@contextlib.contextmanager
def smart_open(filename=None, filemode='w'):
    """
    Return handle to file (if specified) or sys output
    From https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely/17603000
    """

    if filename and filename != '-':
        fh = io.open(filename, newline='', mode=filemode, encoding="utf-8")
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


class OutputWriter:
    def __init__(self, fields):
        self.fields = fields


    def as_row(self, item):
        """
        Converts castaway to an array, which maps to a row in a CSV file
        """
        def value(key):
            return item[key] if key in item else ""

        return [value(field) for field in self.fields]

    def csv_header(self):
        """
        Return header row for CSV file
        """
        return self.fields

    def as_csv(self, items, filename=None, delim=TAB):
        """
        Create a CSV of episodes scraped
        """

        header_rquired = False if not filename or (
            filename and os.path.isfile(filename)) else True
        with smart_open(filename, 'a') as output:
            writer = csv.writer(output, delimiter=delim, lineterminator='\r\n')
            if header_rquired:
                writer.writerow(self.csv_header())

            for item in items:
                writer.writerow(self.as_row(item))


def download_file(url, dir):
    try:
        url_clean = url.strip()
        if url_clean:
            #  os.system('wget --append-output=wget-output.log --no-verbose --directory-prefix=docs %s' % url_clean)
            os.system('wget --no-verbose --directory-prefix=%s %s' %
                      (dir, url_clean))

            doc_name = url_clean.rsplit('/', 1)[-1]
            file = os.path.join('.', dir, doc_name)
            if os.path.isfile(file):
                return file
            else:
                return f'Warning: file not downloaded: {url_clean}'
        else:
            return 'Warning: Blank URL provided'
    except Exception as e:
        return f'Error downloading {url}: {e}'

def get_page(url):
    def page_found(code):
        return code == 200

    response = requests.get(url)

    if not page_found(response.status_code):
        print(f'Warning: status {response.status_code} for {url}')
        return None
    else:
        return BeautifulSoup(response.content, 'html.parser')
