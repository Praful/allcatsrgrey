"""
=============================================================================
File: category_urls.py
Description: Get the URLs for categories from allcatsrgrey.org.uk
Author: Praful https://github.com/Praful/allcatsrgrey
Licence: GPL v3

This uses selenium and the ChromeDriver unlike the other code in the project, which uses just
BeautifulSoup. I couldn't find a way of triggering the change event for the Select control on
the page and submitting the form. 

The get_category_options() method takes a long time to run. So the pre-fetched
category-urls.txt file should be used unless you want to regnerate the file.

This requires Chrome and the ChromeDriver from:
    https://googlechromelabs.github.io/chrome-for-testing/
Change the two paths below to where you saved the chrome driver and chrome.
=============================================================================
"""
# 
#
#
import os
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

def get_category_options(driver, url):
    driver.get(url)
    select_element = driver.find_element(By.NAME, "cat")

    # Create a Select object for the select element
    return Select(select_element)

def category_urls(url, filename=None, create_file=False):
    """Scrape data from the allcatsrgrey.org.uk website.
    Since this is a lengthy process, we check if we've saved the URL in a file 
    unless asked to regenerate. Note that any existing file will be overwritten.
    """
    if not create_file and filename and os.path.isfile(filename):
        return file_to_array(filename, True)

    if create_file and not filename:
        print('No filename provided to create category urls file')
        return []

    print('=============== Getting category URLs')
    result = []    

    webdriver_path = '/opt/chromedriver/chromedriver'
    chrome_binary_path ='/opt/chromedriver/chrome-linux64/chrome'

    # Create a ChromeService instance with the executable path
    service = ChromeService(executable_path=webdriver_path)

    # Create ChromeOptions and set the binary location
    chrome_options = ChromeOptions()
    chrome_options.binary_location = chrome_binary_path

    # Comment this out to disable headless mode and see the browser on screen.
    chrome_options.add_argument("--headless")  # Enable headless mode

    # Create a Chrome webdriver instance with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Create a Select object for the select element
    select = get_category_options(driver, url)
    values = [option.get_attribute("value") for option in select.options]

    # Loop through each option in the select control
    for value in values:
        try:
            #  print(value)
            if value == "-1":
                continue

            # we have to go back to the original page since the select control is 
            # stale after submitting the form.
            select = get_category_options(driver, url)

            select.select_by_value(value)

            # Wait for the page to load; adject if necessary
            driver.implicitly_wait(2) 

            new_url = driver.current_url
            print(new_url)
            result.append(new_url)

            #TODO just for testing
            #  if len(result) >3:
                #  break
        except Exception as e:
            print('Error processing value', e)
            traceback.print_exc()


    if create_file:
        array_to_file(filename, result)

    # Close the browser
    driver.quit()

    return result
