# National Grey Literature Collection

This repo consists of Python scripts to scrape data from The National Grey Literature Collection. The URL of the site is [https://allcatsrgrey.org.uk](https://allcatsrgrey.org.uk).

All the scripts in this repo are available on [GitHub](https://github.com/Praful/allcatsrgrey).

The main scripts all have help for the command line arguments. To see the help, run:

```
python <script name> --help
```

# Installation
The code was tested using [Python 3.11](https://www.python.org/downloads/) on Linux Mint 21.2. However, it should work on any operating system supporting a recent version of Python 3.

To install the required packages, use 
[pip](https://pip.pypa.io/en/stable/installation/) to run: 
```
pip install -r requirements.txt 
```
If you want to scrape documents URLS referenced by categories, you'll need to install the 
Chrome browser and the chrome driver from 
[here](https://googlechromelabs.github.io/chrome-for-testing/) and edit 
`category_urls.py` to set the path of `chrome` and `chromedriver`. By default, the 
code uses the pre-scraped `category-urls.txt` file since it's a lengthy process to 
scrape the category URLs.

# Scripts

The scripts output CSV files. The delimiter is a tab.

The following scripts are included in this repo:

## allcatsgrey_collection.py

This script scrapes data from the [The Collection](https://allcatsrgrey.org.uk/wp/find-grey-literature/) part of the website. This is the main part of the website and consists of about 18,000 records.

If downloads are referenced, the script attempts to download the documents. To do 
this, the script attempts to fix the broken links.

An example of running the script is:

```
python allcatsgrey_collection.py --start-page 1 --end-page 5 --items-per-page 10 --csv output1.csv
```


During testing, I ran the script twice at the same time (in two consoles). One collected pages 1-100 and the other pages 101 to the end. These were the commands used:


```
python allcatsgrey_collection.py --start-page 1 --end-page 100 --items-per-page 100 --csv output1.csv
```

```
python allcatsgrey_collection.py --start-page 101 --end-page 0 --items-per-page 100 --csv output2.csv
```
After that, the two files were merged using 
```
cat output1.csv output2.csv > output.csv
```
in Linux.

When `--end-page` is 0, the script will go to the end of the collection.

Collecting all the indexed data with two scripts running at the same time (as above) 
takes about three hours.

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
documents. There are three routes to these documents, which _all point to the same files_. (For more information, see the section below _Analysis of archive, category, and region data._)

The three paths on the website to the documents are:

1. Archive, eg the Archives section on the left side of [this 
   page](https://allcatsrgrey.org.uk/wp/wpfb-file/cervical_screening_standards_data_report_2018_to_2019-pdf/#wpfb-cat-127).
2. Region data: viewed from the links that appear when you hover the mouse over The Collection top level menu.
3. Category data: viewed from [The 
   Collection](https://allcatsrgrey.org.uk/wp/find-grey-literature/) the page where, 
   on the right hand side, is a drop down menu for selecting a category.

Note, however, that all the documents are available via the archive method. Therefore you never need to run the script using the `category` or `region` options. You don't have to run the `archive` option unless in the unlikely situation that it is updated. The output of the archive files is provided in the output folder.

If you do want to see the output of these options, here are some Examples of collecting data using these three methods:
```
python allcatsgrey_documents.py --method archive --csv archive.csv
python allcatsgrey_documents.py --method region --csv region.csv
python allcatsgrey_documents.py --method category --csv category.csv
```
When running with `--method category`, the script uses the pre-fetched list of 
category URLs in `category-urls.txt`. You can recreate the list by either renaming 
`category-urls.txt` or uncommenting the first line below and commenting out the second line in `allcatsgrey_documents.py`:

```
#  urls = category_urls(CATEGORY_URL, CATEGORY_URL_FILENAME, True )
urls = category_urls(CATEGORY_URL, CATEGORY_URL_FILENAME )
```

In the most recent of `allcatsgrey_documents.py`, the URLs are looked up (following URL redirects) and resolved so that the final URL is shown in the output, which includes the full file name. This makes running the script slow.


### Downloading documents

There are two ways to download documents.

#### Option 1: using `wget`
In the `output` folder is the output of the most archive run. It includes the CSV 
   file and a URL file. The URL list was extracted from the CSV file using command:
```
cat archive-20230917.csv | cut -f4 -d$'\t' >urls.txt
```
With the URL file, you can use the `wget` command to download the documents. Here's an example:
```
wget -N -x -i urls.txt --directory-prefix=downloads -a wget-output.log --show-progress
```
In this example, the command will recreate the directory structure in the URL (`-x`) in the 
`downloads` directory. `wget` output will be _appended_ to `wget-output.log`. Use 
`-o` to overwrite the log file. The `-N` option will download files only if they don't exist locally or are newer than your local copy. This lets you re-run the command without having to edit the `urls.txt` file or to download files you've already downloaded.


This download method is faster than Option 2 below.

#### Option 2: using built-in `--download`
By default, this script _doesn't_ download any documents because there are about 9,900 downloads for the archive section alone. To download documents while scraping the website, use the `--download` switch.

```
python allcatsgrey_documents.py --method archive --csv archive.csv --download
```
If you specify `--download`, the script will download documents into folder 
`downloads`. If the folder doesn't exist, it will be be created. In `downloads`, the 
directory structure of the URL will be created. The script uses the `wget` command to 
download files using similar options to the `wget` command in Option 1 above.

This option is slower than Option 1 because URLs have to be first looked up and 
resolved since most of the raw URLs scraped are redirected. Option 1 uses the 
redirected URLs, which speeds up the process.

_Do not download documents for the `--method category` option._ There are about 96,000 documents! 
Most of them are duplicates. They won't be re-downloaded but all the documents are 
available via the `--method archive` option. However, Option 1 is faster because the documents have already been collected.


### Analysis of archive, category, and region data
On analysis, the documents found via the archive links and the category links are the same once the 
category CSV file is de-duplicated. Therefore, the complete data for the site is the 
collection CSV and the archive CSV. My assumption is that the collection data maps to 
the archive data. That is, the archive documents are some of the documents the 
collection indexes. There are about 18,000 collection items and 9,900 archive 
documents. _Work is required to link The Collection index to the documents._

To summarise: _there is no need to run_ `allcatsfrey_documents.py` with options `--method category` or `--method region` since `--method archive` returns everything.

## category_urls.py

This script gets the URLS for each category. It uses the `selenium` library to get 
the pages. I couldn't work out how to use the `beautifulsoup` library (used by most of the 
code) to submit a form that is submitted in a change event of the `select` control.

This script is called by the `allcatsgrey_documents.py` script. You don't need to 
call it directly.

# Output

The `output` folder contains a zip file of all the data scraped: collection data, 
archive data, category data, and region data.
