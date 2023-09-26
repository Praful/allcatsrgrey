"""
=============================================================================
File: allcatrsgrey_downloads_treeview.py
Description: Scrape the urls of downloadable docs from treeview 
Author: Praful https://github.com/Praful/allcatsrgrey
Licence: GPL v3

This uses selenium and the ChromeDriver unlike the other code in the project, which uses just
BeautifulSoup. I couldn't find a way of triggering the change event for the Select control on
the page and submitting the form. 


This requires Chrome and the ChromeDriver from:
    https://googlechromelabs.github.io/chrome-for-testing/
Change the two paths below to where you saved the chrome driver and chrome.
=============================================================================
"""

import os
import argparse
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select  # Import the Select class
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from utils import *
from bs4 import BeautifulSoup

DEFAULT_SLEEP = 60
HEADER = ['Title', 'Categories', 'URL', 'Error']
DOWNLOADS_TREEVIEW_URL = "https://allcatsrgrey.org.uk/wp/downloads/"

WEBDRIVER_PATH = '/opt/chromedriver/chromedriver'
CHROME_BINARY_PATH = '/opt/chromedriver/chrome-linux64/chrome'


def init_driver():

    # Create a ChromeService instance with the executable path
    service = ChromeService(executable_path=WEBDRIVER_PATH)

    # Create ChromeOptions and set the binary location
    chrome_options = ChromeOptions()
    chrome_options.binary_location = CHROME_BINARY_PATH

    # Comment this out to disable headless mode and see the browser on screen.
    chrome_options.add_argument("--headless")  # Enable headless mode

    # Create a Chrome webdriver instance with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)

    #  driver.implicitly_wait(30)
    return driver


class Scraper:
    def __init__(self, writer, driver, sleep):
        self.writer = writer
        self.driver = driver
        self.sleep = sleep

    def scrape_folder(self, node, node_categories=None):
        categories = ''

        try:
            node_id = node.get_attribute('id')
            print('============ Processing node', node_id)
            button = node.find_element(By.TAG_NAME, 'a')
            button.click()

            category = button.get_attribute("text")
            print(category)
            if node_categories:
                categories = '#'.join((node_categories, category))
            else:
                categories = category

            # provide time to retrieve children
            time.sleep(self.sleep)

            self.scrape_files(node_id, 'li', categories)

        except Exception as e:
            print('Error fetching page', e)
            traceback.print_exc()


        self.process_subfolders(node, categories)

    def process_subfolders(self, parent, categories=None):
        children = parent.find_elements(By.CLASS_NAME, "hasChildren")
        for child in children:
            try:
                self.scrape_folder(child, categories)
            except Exception as e:
                print('Error fetching child node', child, e)
                traceback.print_exc()

    def scrape_files(self, node_id, tag='li', categories=None):

        def is_file(o):
            if o.has_attr('id'):
                return o['id'].startswith('wpfb-file')
            return False

        result = []
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        soup_node = soup.find(tag, id=node_id)
        #  print(soup_node)
        if soup_node:
            #  print(categories, soup_node['id'])
            try:
                children = soup_node.find_all('li')
                #  print(len(children))
                for child in children:
                    if child:
                        #  print('--------------', child)
                        if is_file(child):
                            link = child.find('a')
                            url = link['href']
                            title = link.text
                            print(child['id'], url, title)
                            result.append(
                                {'Title': title, 'Categories': categories, 'URL': url})
            except Exception as e:
                print('Error fetching page', e)
                traceback.print_exc()
            finally:
                self.writer.as_csv(result)

def setup_command_line():
    """
    Define command line switches
    """
    cmdline = argparse.ArgumentParser(
        prog='allcatrsgrey_downloads_treeview.py')
    cmdline.add_argument('--csv', dest='output',
                         help='Filename of CSV file (tab-separated). The file will be appended '
                         'to if it exists (default output is to console)')
    cmdline.add_argument('--sleep', type=int, default=DEFAULT_SLEEP,
                         help=f'Time to pause (in seconds) between fetching pages (default is {DEFAULT_SLEEP} seconds)')

    return cmdline


def main():
    args = setup_command_line().parse_args()

    writer = OutputWriter(HEADER, args.output)
    driver = init_driver()
    scraper = Scraper(writer, driver, args.sleep)

    driver.get(DOWNLOADS_TREEVIEW_URL)
    try:
        treeview = driver.find_element(By.CLASS_NAME, "treeview")
        scraper.scrape_files(treeview.get_attribute('id'), 'ul')
        scraper.process_subfolders(treeview)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
