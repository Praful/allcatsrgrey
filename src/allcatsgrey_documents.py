"""
=============================================================================
File: allcatsrgrey_documents.py
Description: Scrapes informaton about the documents on allcatsrgrey.org.uk using three methods: 
    archive, region and category.
Author: Praful https://github.com/Praful/allcatsrgrey
Licence: GPL v3

=============================================================================
"""

import os
import sys
import traceback
from bs4 import BeautifulSoup
import argparse
import requests
import time
#  sys.path.append(os.path.relpath("./"))
from utils import *
from category_urls import category_urls

DEFAULT_SLEEP = 3
DEFAULT_METHOD = 'archive'
DEFAULT_DOWNLOAD = False
TAB = '\t'
DOWNLOAD_DIR = 'archive-docs'
REGION_URL ='https://allcatsrgrey.org.uk/wp/find-grey-literature/'
ARCHIVE_URL ='https://allcatsrgrey.org.uk/wp/wpfb-file/cervical_screening_standards_data_report_2018_to_2019-pdf/#wpfb-cat-127'
CATEGORY_URL = 'https://allcatsrgrey.org.uk/wp/find-grey-literature/'
CATEGORY_URL_FILENAME = './category-urls.txt'

HEADER = ['Title', 'Date', 'Categories', 'URL', 'Download', 'Error']


import mechanize


def region_urls(url):
    soup = get_page(url)

    if soup is None:
        return []
    
    container = soup.find_all('li', class_='menu-item')
    if container:
        for listitem in container:
            for link in listitem.find_all('a'):
                if link.text == 'The Collection':
                    print("found")
                    ul = listitem.find('ul')
                    return [a['href'] for a in ul.find_all('a')]

    return []

def archive_urls(url):
    soup = get_page(url)

    if soup is None:
        return []

    archive = soup.find('div', id='secondary')
    links = archive.find_all('a')

    if links: 
        return [item['href'] for item in links]

    return []


def get_next_url(soup):
    try:
        button = soup.find('li', class_='previous')
        if button:
            next_url = button.find('a')
            if next_url:
                return next_url['href']
    except Exception as e:
        print('Error getting next url', e)
        traceback.print_exc()

    return None

items_processed = 0

def scrape_articles_from_pages(url, do_download):
    global items_processed
    print('============= Processing page:', url)
    next_url = url
    article_list=[]
    while next_url:
        soup = get_page(next_url)
        print('      ----- Processing next page', next_url)
        if soup:
            articles = soup.find_all('article')
            if articles:
                for article in articles:
                    item = {}
                    try:
                        link = article.find('a')
                        if link:
                            item['URL'] = real_url(link['href'])
                            item['Title'] = link['title']
                        datetime = article.find('time', class_='entry-date published')
                        item['Date'] = datetime['datetime'] if datetime else ''

                        categories = article.find('span', class_='category')
                        if categories:
                            cat_links = categories.find_all('a')
                            if cat_links:
                                item['Categories'] = ';'.join([link.text for link in cat_links])

                        if do_download and 'URL' in item:
                            item['Download'] = download_file(item['URL'], DOWNLOAD_DIR)

                    except Exception as e:
                        print('Error fetching page', url, e)
                        traceback.print_exc()
                        item['Error'] = repr(traceback.format_exception(e))

                    items_processed += 1
                    article_list.append(item)

            next_url = get_next_url(soup)
        else:
            print('Warning: No soup found for archive month url', url)
            break


    print(items_processed, 'items processed')
    return article_list

def scrape_all_articles(csv_filename, sleep, urls, do_download):
    writer = OutputWriter(HEADER, csv_filename)

    for url in urls:
        data=[]
        try:
            data = scrape_articles_from_pages(url, do_download)
            #  break # uncomment to stop after first page (for testing)
        except Exception as e:
            print('Error fetching page', url, e)
            traceback.print_exc()
        finally:
            writer.as_csv(data)

        time.sleep(sleep)

def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(prog='allcatsgrey-documents.py')
    cmdline.add_argument('--csv', dest='output',
                         help='Filename of CSV file (tab-separated). The file will be appended '
                         'to if it exists (default output is to console)')
    cmdline.add_argument('--sleep', type=int, default=DEFAULT_SLEEP,
                         help=f'Time to pause (in seconds) between fetching pages (default is {DEFAULT_SLEEP} seconds)')
    cmdline.add_argument('--url', dest='url', help='URL of the page to scrape. If specified, the other options are ignored.')
    cmdline.add_argument('--method', dest='method',
                         help=f'Grab document data either from archive, region, or category section of website (default is {DEFAULT_METHOD})')
    cmdline.add_argument('--download', dest='download', action='store_true', default=DEFAULT_DOWNLOAD, help=f'Download files (default is {DEFAULT_DOWNLOAD})')

    return cmdline


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()

    if args.url:
        print(scrape_articles_from_pages(args.url, args.download))
    else:
        if args.method == 'archive':
            urls = archive_urls(ARCHIVE_URL)
        elif args.method == 'region':
            urls = region_urls(REGION_URL)
        elif args.method == 'category':
            # uncomment to regenerate category urls. Warning: this is slow!
            #  urls = category_urls(CATEGORY_URL, CATEGORY_URL_FILENAME, True )
            urls = category_urls(CATEGORY_URL, CATEGORY_URL_FILENAME )
        else:
            print('Invalid method specified. Must be archive or region')
            sys.exit(1)

        scrape_all_articles(args.output, args.sleep, urls, args.download)


if __name__ == '__main__':
    main()
