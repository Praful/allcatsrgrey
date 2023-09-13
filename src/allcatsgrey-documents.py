import os
import sys
from bs4 import BeautifulSoup
import csv
import argparse
import contextlib
import io
import time
import traceback
import re
import requests

TOTAL_ITEMS = 18961
DEFAULT_START_PAGE = 1
DEFAULT_END_PAGE = 2  # 0 = all pages
DEFAULT_ITEMS_PER_PAGE = 10
DEFAULT_SLEEP = 3
TAB = '\t'

ALLCATSGREY_COLLECTION_HOME = f'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&pagenum=%s&per_page=%s'


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

    FIELDS=['Index', 'Title','Description','Author','Published','Status','Subject','Category',
            'Media','ISBN','Call Number','Type','Keywords','Download','URL','Error']
        
    def as_row(self, item):
        """
        Converts castaway to an array, which maps to a row in a CSV file
        """
        def value(key):
            return item[key] if key in item else ""

        return [value(field) for field in self.FIELDS]

    def csv_header(self):
        """
        Return header row for CSV file
        """
        return self.FIELDS

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


def download_file(url):
    try:
        url_clean = url.strip()
        if url_clean:
            #  os.system('wget --append-output=wget-output.log --no-verbose --directory-prefix=docs %s' % url_clean)
            os.system('wget --no-verbose --directory-prefix=archive-docs %s' %
                      url_clean)

            doc_name = url_clean.rsplit('/', 1)[-1]
            file = os.path.join('.', 'archive-docs', doc_name)
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


def scrape_archive_urls(url):
    soup = get_page(url)

    if soup == None:
        return {}

    archive = soup.find('div', id='secondary')
    links = archive.find_all('a')
    
    return [item['href'] for item in links]


def clean_string(s):
    if s:
        return s.strip(" :\r\xa0")
    else:
        return s

def get_next_url(soup):
    button = soup.find('li', class_='previous')
    if button:
        next_url = button.find('a')
        if next_url:
            return next_url['href']

    return None

items_processed = 0

def scrape_archive_month(url):
    global items_processed
    print('============= Processing page:', url)
    next_url = url
    while next_url:
        soup = get_page(next_url)
        print('      ----- Processing next page', next_url)
        if soup:
            articles = soup.find_all('article')
            for article in articles:
                print('-------')
                link = article.find('a')
                url = link['href']
                title = link['title']
                datetime = article.find('time', class_='entry-date published')
                if datetime:
                    date = datetime['datetime']
                else:
                    date = ''

                print(title, url, date)
                #  TODO do we need to download these?
                #  download_status = download_file(url)
                categories = article.find_all('span', class_='category')
                for category in categories:
                    links = category.find_all('a')
                    for link in links:
                        print(link.text)
                items_processed += 1
            next_url = get_next_url(soup)
        else:
            print('Warning: No soup found for archive month url', url)

    print(items_processed, 'items processed')





def get_all_data(csv_filename, start_page, end_page, items_per_page, sleep):
    home='https://allcatsrgrey.org.uk/wp/wpfb-file/cervical_screening_standards_data_report_2018_to_2019-pdf/#wpfb-cat-127'


    index_list = scrape_archive_urls(home)
    for url in index_list:
        scrape_archive_month(url)
        #TODO
        #  break # just do first page for now
    

    print('Total items processed:', items_processed)

def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(prog='allcatsgrey-documents.py')
    cmdline.add_argument('--csv', dest='output',
                         help='Filename of CSV file (tab-separated). The file will be appended '
                         'to if it exists (default output is to console)')
    cmdline.add_argument('--start-page', type=int, default=DEFAULT_START_PAGE,
                         help=f'First page to scrape data from (default is {DEFAULT_START_PAGE})')
    cmdline.add_argument('--end-page', type=int, default=DEFAULT_END_PAGE,
                         help=f'Last page to scrape episodes from (default is {DEFAULT_END_PAGE})')
    cmdline.add_argument('--items-per-page', type=int, default=DEFAULT_ITEMS_PER_PAGE,
                         help=f'Fo each page, fetch this many entries (default is {DEFAULT_ITEMS_PER_PAGE})')
    cmdline.add_argument('--sleep', type=int, default=DEFAULT_SLEEP,
                         help=f'Time to pause (in seconds) between fetching pages (default is {DEFAULT_SLEEP} seconds)')
    cmdline.add_argument('--url', dest='url', help='URL of the page to scrape. If specified, the other options are ignored.')

    #  if len(sys.argv) < 2:
    #
        #  cmdline.print_help()
        #  sys.exit(1)

    return cmdline


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()

    if args.url:
        print(scrape_archive_month(args.url))
    else:
        get_all_data(args.output, args.start_page, args.end_page,
                    args.items_per_page, args.sleep)


if __name__ == '__main__':
    main()

#  url = 'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000004'
#  scrape_page_data(url)


#  url = 'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000002'
#  scrape_page_data(url)
#
    #  url = 'http://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000011'
    #  scrape_page_data(url)
