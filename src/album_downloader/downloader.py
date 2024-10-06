import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from album_downloader.fetcher import ImageFetcher  # Correct import

class AlbumDownloader:

    def __init__(self, album_url):
        self.album_url = album_url
        self.album_name = None
        self.total_images = 0

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.fetcher = ImageFetcher()  # Initialize the ImageFetcher

    def fetch_album_info(self):
        # Log the start of the album information fetching
        logging.info(f"Fetching album information from: {self.album_url}")

        try:
            # Make a request to the album page
            response = requests.get(self.album_url)
            response.raise_for_status()  # Raise an error for bad HTTP responses

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the album name
            bread_crumb = soup.find('div', class_='png bread')
            if bread_crumb:
                self.album_name = bread_crumb.get_text().split('>')[-1].strip()
                logging.info(f"Album name extracted: {self.album_name}")

            # Extract the total number of images
            page_info = soup.find('div', class_='asTBcell uwconn')
            if page_info:
                page_count_label = page_info.find('label', string=lambda text: '頁數' in text)
                if page_count_label:
                    self.total_images = int(page_count_label.get_text().split('：')[1].replace('P', '').strip())
                    logging.info(f"Total number of images: {self.total_images}")

        except requests.RequestException as e:
            logging.error(f"Failed to fetch album info: {e}")

    def download_images(self):
        # Log the start of the image downloading process
        logging.info(f"Starting the download of images for album: {self.album_name}")

        # Create a folder for the album
        download_dir = os.path.join('.', 'downloaded', self.album_name)
        os.makedirs(download_dir, exist_ok=True)

        # Find the first image URL from the album page and extract base URL logic
        first_image_url = self._find_first_image_url()
        if not first_image_url:
            logging.error("Failed to find the first image URL.")
            return

        # Extract the base URL and file parts
        base_url, base_filename = os.path.split(first_image_url)
        filename_core, _ = os.path.splitext(base_filename)

        # Initialize counters and trackers
        success_count = 0
        file_extensions = ['.jpg', '.png', '.webp', '.jpeg', '.gif']
        tried_filenames = set()  # Set to track filenames that have already been attempted
        most_likely_extension = None  # Memorize the most likely file extension

        # Iterate until the number of downloaded images matches the total number
        while success_count < self.total_images:
            # Generate filename variations
            variations = self._generate_filename_variations(filename_core)

            # Track if an image was downloaded in this iteration
            image_downloaded = False

            # Try each variation exactly once
            for variation in variations:
                # Skip this variation if it's already been tried
                if variation in tried_filenames:
                    continue

                # List of extensions to try, prioritize the most likely one if known
                extensions_to_try = file_extensions
                if most_likely_extension:
                    # Move the most likely extension to the front of the list
                    extensions_to_try = [most_likely_extension] + [ext for ext in file_extensions if ext != most_likely_extension]

                # Try each file extension for this variation
                for ext in extensions_to_try:
                    # Construct the potential URL and file path
                    image_url = f"{base_url}/{variation}{ext}"
                    file_name = f"{variation}{ext}"
                    save_path = os.path.join(download_dir, file_name)

                    # Attempt to download the image using ImageFetcher
                    if self.fetcher.fetch_image(image_url, save_path):
                        success_count += 1
                        image_downloaded = True
                        filename_core = variation  # Update the base filename for the next iteration
                        most_likely_extension = ext  # Memorize this extension as most likely
                        break  # Exit the extension loop on success

                # Add the variation to the set of tried filenames
                tried_filenames.add(variation)

                # If an image was downloaded successfully, break and move to the next primary image
                if image_downloaded:
                    break

            # If no image was downloaded for any variation, move to the next primary image
            if not image_downloaded:
                logging.error(f"Failed to download any image for variations starting with '{filename_core}'")
                # Increment the core filename to force the loop to the next logical set (e.g., move from `01_01` to `02_01`)
                filename_core = self._increment_primary_core(filename_core)

        # Log the completion of the download process
        logging.info(f"Downloaded {success_count}/{self.total_images} images successfully.")

    def _increment_primary_core(self, filename_core):
        # Increment the first set of digits found in the filename core (e.g., '01_01' -> '02_01')
        num_pattern = re.compile(r'(\d+)')
        matches = list(num_pattern.finditer(filename_core))
        if matches:
            # Increment the first set of digits in the filename
            first_match = matches[0]
            num_str = first_match.group()
            num_len = len(num_str)
            incremented_num = str(int(num_str) + 1).zfill(num_len)
            # Construct the new filename with the incremented number
            new_core = filename_core[:first_match.start()] + incremented_num + filename_core[first_match.end():]
            return new_core
        else:
            # If no digits found, append '_01' to force a change
            return filename_core + '_01'

    def _generate_filename_variations(self, filename_core):
        # Generate variations of the filename by incrementing numbers in the string
        variations = [filename_core]  # Start with the original filename
        num_pattern = re.compile(r'(\d+)')

        # Find all numbers in the filename core
        matches = list(num_pattern.finditer(filename_core))

        # Increment only the last set of digits first (e.g., '01_01' to '01_02', '01_03', etc.)
        if matches:
            last_match = matches[-1]
            num_str = last_match.group()
            num_len = len(num_str)

            # Try incrementing the last set of digits
            for increment in range(1, 4):
                incremented_num = str(int(num_str) + increment).zfill(num_len)
                # Replace the last number in the string to form a new variation
                variation = (filename_core[:last_match.start()] + incremented_num +
                             filename_core[last_match.end():])
                variations.append(variation)

        return variations

    def _find_first_image_url(self):
        try:
            # Make a request to the album page
            response = requests.get(self.album_url)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the first `li` element with class `li tb gallary_item`
            gallery_item = soup.find('li', class_='li tb gallary_item')
            if gallery_item:
                # Find the anchor tag containing the image page URL
                anchor = gallery_item.find('a', href=True)
                if anchor:
                    # Construct the full URL of the image page
                    first_image_page_url = 'https://xxxx.com' + anchor['href']

                    # Now visit the first image page to extract the actual image URL
                    return self._extract_image_src_from_page(first_image_page_url)

            logging.error("Failed to locate the first image URL in the album page.")
            return None

        except requests.RequestException as e:
            logging.error(f"Error occurred while fetching the album page: {e}")
            return None

    def _extract_image_src_from_page(self, image_page_url):
        try:
            # Make a request to the image page
            response = requests.get(image_page_url)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the div with id `photo_body` and the image inside it
            photo_body = soup.find('div', id='photo_body')
            if photo_body:
                image_tag = photo_body.find('img', id='picarea')
                if image_tag and 'src' in image_tag.attrs:
                    # Construct the full URL for the image
                    image_src = image_tag['src']
                    if image_src.startswith('//'):
                        image_src = 'https:' + image_src
                    elif image_src.startswith('/'):
                        image_src = 'https://xxxx.com' + image_src
                    logging.info(f"First image source found: {image_src}")
                    return image_src

            logging.error("Failed to extract the image source from the image page.")
            return None

        except requests.RequestException as e:
            logging.error(f"Error occurred while fetching the image page: {e}")
            return None


