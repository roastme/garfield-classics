import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import time
import re
import random
from PIL import Image
from io import BytesIO
import logging

BASE_URL = "https://www.gocomics.com/garfield-classics/"
WAYBACK_URL = "http://web.archive.org/web/"
DOWNLOAD_FOLDER = 'garfield_classics_archive'
LOW_RES_FOLDER = 'garfield_classics_low_res'
FULL_LOG_FILE = 'garfield_classics_full.log'
ERROR_LOG_FILE = 'garfield_classics_errors.log'
START_DATE = datetime(2020, 6, 1)  # Garfield Classics introduction date
END_DATE = datetime(2023, 12, 2)  # Last known date before delisting
DELAY = 10  # Delay between requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for downloading
CONNECTION_RETRIES = 3  # Retries for connection errors
HIGH_RES_CUTOFF = datetime(2017, 2, 1)  # Date when high-res images became consistently available

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(FULL_LOG_FILE)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_handler = logging.FileHandler(ERROR_LOG_FILE)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(error_handler)

def get_wayback_url(date):
    formatted_date = date.strftime("%Y%m%d")
    url = f"{WAYBACK_URL}{formatted_date}/{BASE_URL}{date.strftime('%Y/%m/%d')}"
    return url

def extract_comic_url(html_content):
    # Method 1: Direct search for assets.amuniversal.com link (preferring 900px version)
    match = re.search(r'(https?://assets\.amuniversal\.com/[^"\']+)', html_content)
    if match:
        url = match.group(1)
        # Try to modify URL for 900px version
        return url.replace('width=900', '')  # Remove any existing width parameter
    
    # Method 2: Search for image URL in a relevant div
    soup = BeautifulSoup(html_content, 'html.parser')
    comic_div = soup.find('div', class_='comic__image')
    if comic_div:
        img_tag = comic_div.find('img')
        if img_tag and 'src' in img_tag.attrs:
            return img_tag['src'].replace('width=900', '')  # Remove any existing width parameter
    
    # Method 3: General search for image URLs
    img_urls = re.findall(r'(https?://[^"\']+\.(?:gif|png|jpg|jpeg))', html_content)
    for url in img_urls:
        if 'assets.amuniversal.com' in url:
            return url.replace('width=900', '')  # Remove any existing width parameter
    
    return None

def get_comic_url(date):
    url = get_wayback_url(date)
    logger.info(f"Checking page: {url}")
    for _ in range(CONNECTION_RETRIES):
        try:
            response = requests.get(url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                comic_url = extract_comic_url(response.text)
                if comic_url:
                    logger.info(f"Found comic URL for {date.strftime('%Y-%m-%d')}: {comic_url}")
                    return comic_url
                else:
                    logger.error(f"Comic URL not found for {date.strftime('%Y-%m-%d')} on the Wayback Machine page")
                    return None
            elif response.status_code == 404:
                logger.error(f"Page not found for {date.strftime('%Y-%m-%d')} on the Wayback Machine")
                return None
            else:
                logger.error(f"Unexpected status code {response.status_code} for {date.strftime('%Y-%m-%d')}")
        except requests.RequestException as e:
            logger.error(f"Connection error for {date.strftime('%Y-%m-%d')}: {str(e)}")
        time.sleep(random.uniform(3, 15))  # Random delay before retry
    logger.error(f"Max retries exceeded for {date.strftime('%Y-%m-%d')}")
    return None

def download_image(url, date, folder=DOWNLOAD_FOLDER):
    filename = f"gacl{date.strftime('%y%m%d')}.gif"
    file_path = os.path.join(folder, filename)
    low_res_path = os.path.join(LOW_RES_FOLDER, filename)
    
    if os.path.exists(file_path) or os.path.exists(low_res_path):
        logger.info(f"Image for {date.strftime('%Y-%m-%d')} already exists. Skipping.")
        return True

    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                width, height = img.size
                
                # Check if it's a low-res image before the cutoff date
                if date < HIGH_RES_CUTOFF.date() and width <= 600:
                    file_path = low_res_path
                    if not os.path.exists(LOW_RES_FOLDER):
                        os.makedirs(LOW_RES_FOLDER)
                
                img.save(file_path)
                logger.info(f"Successfully downloaded: {filename} (Size: {width}x{height})")
                return True
            else:
                logger.error(f"Failed to download image for {date.strftime('%Y-%m-%d')}. Status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Request exception while downloading image for {date.strftime('%Y-%m-%d')}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while downloading image for {date.strftime('%Y-%m-%d')}: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(random.uniform(1, 3))
    return False

def read_dates_from_file(filename='garfield_dates.txt'):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main():
    dates = read_dates_from_file()
    for date_str in dates:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            logger.info(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
            
            filename = f"gacl{current_date.strftime('%y%m%d')}.gif"
            if os.path.exists(os.path.join(DOWNLOAD_FOLDER, filename)) or \
               os.path.exists(os.path.join(LOW_RES_FOLDER, filename)):
                logger.info(f"Image for {current_date.strftime('%Y-%m-%d')} already exists. Skipping.")
                continue
            
            comic_url = get_comic_url(current_date)
            
            if comic_url:
                success = download_image(comic_url, current_date)
                if not success:
                    logger.error(f"Failed to download comic for {current_date.strftime('%Y-%m-%d')} after multiple attempts")
            else:
                logger.warning(f"No comic found for {current_date.strftime('%Y-%m-%d')}")
            
            time.sleep(random.uniform(DELAY, DELAY + 1))
        except ValueError:
            logger.error(f"Invalid date format in file: {date_str}")
    
    logger.info("Finished processing all dates from the file")

if __name__ == "__main__":
    logger.info("Starting Garfield Classics archiving process")
    main()
    logger.info("Archiving process completed")
    print(f"\nArchiving complete. Low-resolution images (if any) can be found in the '{LOW_RES_FOLDER}' folder.")
    print(f"Check '{FULL_LOG_FILE}' for full logs and '{ERROR_LOG_FILE}' for error logs.")
        