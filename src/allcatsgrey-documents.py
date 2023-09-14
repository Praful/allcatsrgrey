import os
import sys
import traceback
from bs4 import BeautifulSoup
import argparse
import requests
import time
#  sys.path.append(os.path.relpath("./"))
from utils import *

DEFAULT_SLEEP = 3
DEFAULT_METHOD = 'archive'
TAB = '\t'
DOWNLOAD_DIR = 'archive-docs'
REGION_URL ='https://allcatsrgrey.org.uk/wp/find-grey-literature/'
ARCHIVE_URL ='https://allcatsrgrey.org.uk/wp/wpfb-file/cervical_screening_standards_data_report_2018_to_2019-pdf/#wpfb-cat-127'

HEADER = ['Title', 'Date', 'Categories', 'URL', 'Error']

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
    button = soup.find('li', class_='previous')
    if button:
        next_url = button.find('a')
        if next_url:
            return next_url['href']

    return None

items_processed = 0

def scrape_articles_from_pages(url):
    global items_processed
    print('============= Processing page:', url)
    next_url = url
    article_list=[]
    while next_url:
        soup = get_page(next_url)
        print('      ----- Processing next page', next_url)
        if soup:
            articles = soup.find_all('article')
            for article in articles:
                item = {}
                try:
                    link = article.find('a')
                    if link:
                        item['URL'] = link['href']
                        item['Title'] = link['title']
                    datetime = article.find('time', class_='entry-date published')
                    item['Date'] = datetime['datetime'] if datetime else ''

                    #  TODO do we need to download these?
                    #  download_status = download_file(url, DOWNLOAD_DIR)
                    categories = article.find('span', class_='category')
                    if categories:
                        cat_links = categories.find_all('a')
                        if cat_links:
                            item['Categories'] = '\n'.join([link.text for link in cat_links])
                except Exception as e:
                    print('Error fetching page', url, e)
                    traceback.print_exc()
                    item['Error'] = repr(traceback.format_exception(e))

                items_processed += 1
                article_list.append(item)

            next_url = get_next_url(soup)
        else:
            print('Warning: No soup found for archive month url', url)


    print(items_processed, 'items processed')
    return article_list

def scrape_all_articles(csv_filename, sleep, urls):
    writer = OutputWriter(HEADER)

    for url in urls:
        data=[]
        try:
            data = scrape_articles_from_pages(url)
            #TODO
            #  break # just do first page for now
        except Exception as e:
            print('Error fetching page', url, e)
            traceback.print_exc()
        finally:
            writer.as_csv(data, csv_filename)

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
                         help=f'Grab document data either from archive or region section of website (default is {DEFAULT_METHOD})')

    return cmdline


def main():
    """
    Processing begins here if script run directly
    """
    args = setup_command_line().parse_args()

    if args.url:
        print(scrape_articles_from_pages(args.url))
    else:
        if args.method == 'archive':
            urls = archive_urls(ARCHIVE_URL)
        elif args.method == 'region':
            urls = region_urls(REGION_URL)
        else:
            print('Invalid method specified. Must be archive or region')
            sys.exit(1)

        scrape_all_articles(args.output, args.sleep, urls)


if __name__ == '__main__':
    main()

