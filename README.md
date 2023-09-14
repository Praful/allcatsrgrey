# National Grey Literature Collection

This repo consists of Python scripts to scrape data from The National Grey Literature Collection. The URL of the site is [https://allcatsrgrey.org.uk](https://allcatsrgrey.org.uk).

All the scripts in this repo are available on [GitHub](https://github.com/Praful/allcatsrgrey).

The main scripts all have help for the command line arguments. To see the help, run:

```
python <script name> --help
```

# Installation
The code was test using [Python 3.11](https://www.python.org/downloads/) on Linux Mint 21.2.

To install the required packages, use 
[pip](https://pip.pypa.io/en/stable/installation/) to run: 
```
pip install -r requirements.txt 
```
If you want to access documents referenced by categories, you'll need to install the 
Chrome and the chrome driver from [here](https://googlechromelabs.github.io/chrome-for-testing/) and edit `category_urls.py` to set the path of `chrome` and `chromedriver`.

# Scripts

The output of the scripts is a CSV file. The delimiter is a tab.

The following scripts are included in this repo:

## allcatsgrey_collection.py

This script scrapes data from the [The Collection](https://allcatsrgrey.org.uk/wp/find-grey-literature/) part of the website. This is the main part of the website and consists of about 18,000 records.

If downloads are referenced, the script attempts to download the documents. To do 
this, the script attempts to fix the broken links.

An example of running the script is:

```
python allcatsgrey_collection.py --start-page 1 --end-page 5 --items-per-page 10 --csv output1.csv
```


During testing, I ran the script twice at the same time (in two consoles). One collected pages 1-100 and the pages 101 to the end. These were the commands used:


```
python allcatsgrey_collection.py --start-page 1 --end-page 100 --items-per-page 100 --csv output1.csv
```

```
python allcatsgrey_collection.py --start-page 101 --end-page 0 --items-per-page 100 --csv output1.csv
```

When `--end-page` is 0, the script will go to the end of the collection.

If you want to check a page is being scraped correctly, you can run:

```
python allcatsgrey_collection.py --url <url of page>
```
such as:

```
python allcatsgrey_collection.py --url 'https://allcatsrgrey.org.uk/wp/find-grey-literature/?searchby=title&searchbox&weblib_orderby=barcode&weblib_order=ASC&barcode=0000000000000010'
```
## allcatsgrey_documents.py

This script scrapes data from various parts of the website that have downloadable 
documents. There are three sources of these documents:

1. archive, eg the Archives section on the left side of [this 
   page](https://allcatsrgrey.org.uk/wp/wpfb-file/cervical_screening_standards_data_report_2018_to_2019-pdf/#wpfb-cat-127)
2. region data: viewed from the links that appear when you hover the mouse over The Collection top level menu.
3. category data: viewed from [The Collection](https://allcatsrgrey.org.uk/wp/find-grey-literature/), the page on the right hand side by selecting 
   a category fomr the drop down menu.

The documents found can be downloaded but this script _doesn't_ download them because 
there, for example, about 10,000 downloads for the archive section alone.

Examples of collecting data usng these three methods:
```
python allcatsgrey_documents.py --method archive --csv archive.csv
python allcatsgrey_documents.py --method region --csv region.csv
python allcatsgrey_documents.py --method category --csv category.csv
```
When running with `--method category`, the script uses the pre-fetched list of 
category urls in `category-urls.txt`. You can re-create the list by uncommenting the 
first line below and commenting out the second line in `allcatsgrey_documents.py`:

```
#  urls = category_urls(CATEGORY_URL, CATEGORY_URL_FILENAME, True )
urls = category_urls(CATEGORY_URL, CATEGORY_URL_FILENAME )
```


## category_urls.py

This scripts gets the URLS for each category. It uses the `selenium` library to get 
the URLs. I couldn't work out how to use the `beautifulsoup` (used by most of the 
code) to submit a form that is submitted in a change event of the `select` control.

This script is called by the `allcatsgrey_documents.py` script.
