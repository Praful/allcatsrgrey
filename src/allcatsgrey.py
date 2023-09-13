import os
import sys
import requests
from bs4 import BeautifulSoup
import csv
import argparse
import contextlib
import io
import time
import traceback
import re
from utils import *

TOTAL_ITEMS = 18961
DEFAULT_START_PAGE = 1
DEFAULT_END_PAGE = 2  # 0 = all pages
DEFAULT_ITEMS_PER_PAGE = 10
DEFAULT_SLEEP = 3
DOWNLOAD_DIR = 'docs'
HEADER=['Index', 'Title','Description','Author','Published','Status','Subject','Category',
            'Media','ISBN','Call Number','Type','Keywords','Download','URL','Error']
ALLCATSGREY_COLLECTION_HOME = f'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&pagenum=%s&per_page=%s'



def scrape_index_data(url):
    soup = get_page(url)

    if soup == None:
        return {}

    items = soup.find_all('div', class_='weblib-item-row')

    for item in items:
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

def scrape_page_data(url, index=1):
    data = {}
    data['URL'] = url
    data['Index'] = index

    try:
        soup = get_page(url)
        if not soup:
            raise Exception(f'Page not found: {url}')

        items = soup.find_all('span', class_='weblib-item-content-element')
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
        a= [c for c in keywords]
        if keywords:
            #  print(list(keywords.text))
            #  print(ctrl_chars(keywords.text))
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

            data['Download'] = download_file(download_url, DOWNLOAD_DIR)

    except Exception as e:
        traceback.print_exc()
        data['Error'] = repr(traceback.format_exception(e))

    if 'Title' in data:
        print(index, ' -- Retrieved title:', data['Title'])

    return data


def get_all_data(csv_filename, start_page, end_page, items_per_page, sleep):

    calc_end_page = (TOTAL_ITEMS//items_per_page) + \
        1 if end_page == 0 else end_page

    writer = OutputWriter(HEADER)

    for page in range(start_page, calc_end_page + 1):
        print('============= Processing page', page)
        url = ALLCATSGREY_COLLECTION_HOME % (page, items_per_page)

        index = (page-1) * items_per_page + 1
        index_list = scrape_index_data(url)
        page_data = []
        try:
            for i, item in enumerate(index_list):
                try:
                    page_data.append(scrape_page_data(item['url'], index + i))
                except Exception as e:
                    print('Error fetching page', item, e)
                    traceback.print_exc()
        finally:
            writer.as_csv(page_data, csv_filename)

        time.sleep(sleep)


def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(prog='allcatsgrey.py')
    cmdline.add_argument('--csv', dest='output',
                         help='Filename of CSV file (tab-separated). The file will be appended '
                         'to if it exists (default output is to console)')
    cmdline.add_argument('--start-page', type=int, default=DEFAULT_START_PAGE,
                         help=f'First page to scrape data from (default is {DEFAULT_START_PAGE})')
    cmdline.add_argument('--end-page', type=int, default=DEFAULT_END_PAGE,
                         help=f'Last page to scrape episodes from (default is {DEFAULT_END_PAGE})')
    cmdline.add_argument('--items-per-page', type=int, default=DEFAULT_ITEMS_PER_PAGE,
                         help=f'For each page, fetch this many entries (default is {DEFAULT_ITEMS_PER_PAGE})')
    cmdline.add_argument('--sleep', type=int, default=DEFAULT_SLEEP,
                         help=f'Time to pause (in seconds) between fetching pages (default is {DEFAULT_SLEEP} seconds)')
    cmdline.add_argument('--url', dest='url', help='URL of the page to scrape. If specified, the other options are ignored.')


    return cmdline


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()

    if args.url:
        print(scrape_page_data(args.url))
    else:
        get_all_data(args.output, args.start_page, args.end_page,
                    args.items_per_page, args.sleep)


if __name__ == '__main__':
    main()

