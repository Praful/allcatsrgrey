import os
import sys
import requests
from bs4 import BeautifulSoup
import csv
import argparse
import contextlib
import io
import time
# import html
import traceback
# from datetime import datetime

TOTAL_ITEMS = 18961
DEFAULT_START_PAGE = 1
DEFAULT_END_PAGE = 0  # 0 = all pages
DEFAULT_ITEMS_PER_PAGE = 100
DEFAULT_SLEEP = 3
TAB = '\t'

ALLCATSGREY_COLLECTION_HOME = f'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&pagenum=%s&per_page=%s'


def is_blank(s):
    return not (s and s.strip())


@contextlib.contextmanager
def smart_open(filename=None, filemode='w'):
    """
    Return handle to file (if specified) or sys output
    From https://stackoverflow.com/questions/17602878/how-to-handle-both-with-open-and-sys-stdout-nicely/17603000
    """

    if filename and filename != '-':
        #  fh = open(filename, 'w')
        fh = io.open(filename, newline='', mode=filemode, encoding="utf-8")
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


class OutputWriter:

    def as_row(self, item, index):
        """
        Converts castaway to an array, which maps to a row in a CSV file
        """
        def value(key):
            return item[key] if key in item else ""

        result = []

        result.append(index)
        result.append(value('Title'))
        result.append(value('Description'))
        result.append(value('Download'))
        result.append(value('Author'))
        result.append(value('Published'))
        result.append(value('Status'))
        result.append(value('Media'))
        result.append(value('Call Number'))
        result.append(value('Type'))
        result.append(value('Keywords'))
        result.append(value('URL'))

        return result

    def csv_header(self):
        """
        Return header row for CSV file
        """
        result = []
        result.append('')
        result.append('Title')
        result.append('Description')
        result.append('Document')
        result.append('Author')
        result.append('Published')
        result.append('Status')
        result.append('Media')
        result.append('Call Number')
        result.append('Type')
        result.append('Keywords')
        result.append('URL')

        return result

    def as_csv(self, items, index, filename=None, delim=TAB):
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
                writer.writerow(self.as_row(item, index))
                index += 1


def get_page(url):
    def page_found(code):
        return code == 200

    response = requests.get(url)

    if not page_found(response.status_code):
        print(f'Warning: status {response.status_code} for {url}')
        return None
    else:
        return BeautifulSoup(response.content, 'html.parser')


def scrape_index_data(url):
    #  response = requests.get(url)
    #  soup = BeautifulSoup(response.content, 'html.parser')
    soup = get_page(url)

    if soup == None:
        return {}

    items = soup.find_all('div', class_='weblib-item-row')

    for item in items:
        #  print(40 * "-")
        spans = item.find_all('span')
        url = spans[2].a['href']
        title = spans[2].a.text
        brs = item.find_all('br')
        source = brs[0].nextSibling.text

        call_number_desc = brs[1].nextSibling.text.split('\xa0')
        if len(call_number_desc) == 2:
            call_number = call_number_desc[1]
        else:
            call_number = ''

        data = {
            'title': title,
            'url': url,
            'source': source,
            'call_number': call_number
        }

        yield data


def clean_string(s):
    if s:
        return s.strip(" :\r\xa0")
    else:
        return s


def scrape_page_data(url):
    #  print(40 * "-")
    #  print('Getting item', url)

    soup = get_page(url)
    if not soup:
        print(f'Page not found: {url}')
        return {}

    items = soup.find_all('span', class_='weblib-item-content-element')
    data = {}
    data['URL'] = url
    content = None
    for item in items:
        heading = clean_string(
            item.find('span', class_='weblib-item-left-head').text)

        value = ""
        tag = 'div' if heading == 'Description' else 'span'
        content = item.find(tag, class_='weblib-item-left-content')
        if content:
            value = clean_string(content.text)

        data[heading] = value

    keywords = soup.find('p', class_='weblib-item-keyword-list')
    if keywords:
        data['Keywords'] = clean_string(keywords.text)

    if content and 'Download Item' in content.text:
        download_url = content.a['href']
        if download_url.startswith('http://allcatsrgrey.org.uk/wp/download/'):
            # The download urls are wrong: the urls should be
            # #http://allcatsrgrey.org.uk/wp/downloads/. However, correcting it takes you
            # to another webpage with information about the document. You then have to
            # click on a link to get the actual document.
            corrected_url = download_url.replace('download', 'downloads')
            # get page describing document we want to download
            soup2 = get_page(corrected_url)
            # now get the url for the document to be downloaded
            if soup2:
                download = soup2.find('a', class_='wpfb-flatbtn')
                if download:
                    download_url = download['href']

        data['Download'] = download_file(download_url)

    if 'Title' in data:
        print('-- Retrieved title:', data['Title'])

    return data


def download_file(url):
    #  print('Downloading %s' % url)
    try:
        url_clean = url.strip()
        if url_clean:
            #  os.system('wget --append-output=wget-output.log --no-verbose --directory-prefix=docs %s' % url_clean)
            os.system('wget --no-verbose --directory-prefix=docs %s' %
                      url_clean)

            doc_name = url_clean.rsplit('/', 1)[-1]
            file = os.path.join('.', 'docs', doc_name)
            #  print(file)
            if os.path.isfile(file):
                return file
            else:
                #  print('Warning: file not downloaded: ', url_clean)
                return f'Warning: file not downloaded: {url_clean}'
        else:
            #  print('Warning: Blank URL provided')
            return 'Warning: Blank URL provided'
    except Exception as e:
        return f'Error downloading {url}: {e}'


def get_all_data(csv_filename, start_page, end_page, items_per_page, sleep):

    calc_end_page = (TOTAL_ITEMS//items_per_page) + \
        1 if end_page == 0 else end_page

    writer = OutputWriter()

    for page in range(start_page, calc_end_page + 1):
        print('============= Processing page', page)
        url = ALLCATSGREY_COLLECTION_HOME % (page, items_per_page)
        #  print(url)
        index = (page-1) * items_per_page + 1
        index_list = scrape_index_data(url)
        page_data = []
        try:
            for item in index_list:
                #  print(item)
                try:
                    page_data.append(scrape_page_data(item['url']))
                except Exception as e:
                    print('Error fetching page', item, e)
                    traceback.print_exc()
        finally:
            writer.as_csv(page_data, index, csv_filename)

        time.sleep(sleep)


def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(prog='allcatsgrey web scraper')
    cmdline.add_argument('--csv', dest='output',
                         help='Filename of CSV file (tab-separated). The file will be appended '
                         'to if it exists (default output is to console)')
    cmdline.add_argument('--start-page', type=int, default=DEFAULT_START_PAGE,
                         help=f'First page to scrape episodes from (default is {DEFAULT_START_PAGE})')
    cmdline.add_argument('--end-page', type=int, default=DEFAULT_END_PAGE,
                         help=f'Last page to scrape episodes from (default is {DEFAULT_START_PAGE})')
    cmdline.add_argument('--items-per-page', type=int, default=DEFAULT_ITEMS_PER_PAGE,
                         help=f'Fo each page, fetch this many entries (default is {DEFAULT_ITEMS_PER_PAGE})')
    cmdline.add_argument('--sleep', type=int, default=DEFAULT_SLEEP,
                         help=f'Time to pause (in seconds) between fetching pages (default is {DEFAULT_SLEEP} seconds)')

    return cmdline


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()
    get_all_data(args.output, args.start_page, args.end_page,
                 args.items_per_page, args.sleep)


if __name__ == '__main__':
    main()

#  url = 'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000004'
#  scrape_page_data(url)


#  url = 'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000002'
#  scrape_page_data(url)
#
    url = 'http://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000011'
    #  scrape_page_data(url)
