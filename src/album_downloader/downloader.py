import os
import re
import logging
import cloudscraper
from bs4 import BeautifulSoup
from album_downloader.fetcher import ImageFetcher

class AlbumDownloader:

    def __init__(self, album_url):
        self.album_url = album_url
        self.album_name = None
        self.total_images = 0

        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.fetcher = ImageFetcher()
        self.scraper = cloudscraper.create_scraper()

    def fetch_album_info(self):
        logging.info(f"Fetching album information from: {self.album_url}")

        try:
            response = self.scraper.get(self.album_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            bread_crumb = soup.find('div', class_='png bread')
            if bread_crumb:
                self.album_name = bread_crumb.get_text().split('>')[-1].strip()
                logging.info(f"Album name extracted: {self.album_name}")

            page_info = soup.find('div', class_='asTBcell uwconn')
            if page_info:
                page_count_label = page_info.find('label', string=lambda text: '頁數' in text)
                if page_count_label:
                    self.total_images = int(page_count_label.get_text().split('：')[1].replace('P', '').strip())
                    logging.info(f"Total number of images: {self.total_images}")

        except Exception as e:
            logging.error(f"Failed to fetch album info: {e}")

    def download_images(self):
        logging.info(f"Starting the download of images for album: {self.album_name}")

        download_dir = os.path.join('.', 'downloaded', self.album_name)
        os.makedirs(download_dir, exist_ok=True)

        first_image_url = self._find_first_image_url()
        if not first_image_url:
            logging.error("Failed to find the first image URL.")
            return

        base_url, base_filename = os.path.split(first_image_url)
        filename_core, _ = os.path.splitext(base_filename)

        success_count = 0
        file_extensions = ['.jpg', '.png', '.webp', '.jpeg', '.gif']
        tried_filenames = set()
        most_likely_extension = None

        while success_count < self.total_images:
            variations = self._generate_filename_variations(filename_core)
            image_downloaded = False

            for variation in variations:
                if variation in tried_filenames:
                    continue

                extensions_to_try = file_extensions
                if most_likely_extension:
                    extensions_to_try = [most_likely_extension] + [ext for ext in file_extensions if ext != most_likely_extension]

                for ext in extensions_to_try:
                    image_url = f"{base_url}/{variation}{ext}"
                    file_name = f"{variation}{ext}"
                    save_path = os.path.join(download_dir, file_name)

                    if self.fetcher.fetch_image(image_url, save_path):
                        success_count += 1
                        image_downloaded = True
                        filename_core = variation
                        most_likely_extension = ext
                        break

                tried_filenames.add(variation)

                if image_downloaded:
                    break

            if not image_downloaded:
                logging.error(f"Failed to download any image for variations starting with '{filename_core}'")
                filename_core = self._increment_primary_core(filename_core)

        logging.info(f"Downloaded {success_count}/{self.total_images} images successfully.")

    def _increment_primary_core(self, filename_core):
        num_pattern = re.compile(r'(\d+)')
        matches = list(num_pattern.finditer(filename_core))
        if matches:
            first_match = matches[0]
            num_str = first_match.group()
            num_len = len(num_str)
            incremented_num = str(int(num_str) + 1).zfill(num_len)
            new_core = filename_core[:first_match.start()] + incremented_num + filename_core[first_match.end():]
            return new_core
        else:
            return filename_core + '_01'

    def _generate_filename_variations(self, filename_core):
        variations = [filename_core]
        num_pattern = re.compile(r'(\d+)')

        matches = list(num_pattern.finditer(filename_core))

        if matches:
            last_match = matches[-1]
            num_str = last_match.group()
            num_len = len(num_str)

            for increment in range(1, 4):
                incremented_num = str(int(num_str) + increment).zfill(num_len)
                variation = (filename_core[:last_match.start()] + incremented_num + filename_core[last_match.end():])
                variations.append(variation)

        return variations

    def _find_first_image_url(self):
        try:
            response = self.scraper.get(self.album_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            gallery_item = soup.find('li', class_='li tb gallary_item')
            if gallery_item:
                anchor = gallery_item.find('a', href=True)
                if anchor:
                    first_image_page_url = 'https://xxxx.com' + anchor['href']
                    return self._extract_image_src_from_page(first_image_page_url)

            logging.error("Failed to locate the first image URL in the album page.")
            return None

        except Exception as e:
            logging.error(f"Error occurred while fetching the album page: {e}")
            return None

    def _extract_image_src_from_page(self, image_page_url):
        try:
            response = self.scraper.get(image_page_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            photo_body = soup.find('div', id='photo_body')
            if photo_body:
                image_tag = photo_body.find('img', id='picarea')
                if image_tag and 'src' in image_tag.attrs:
                    image_src = image_tag['src']
                    if image_src.startswith('//'):
                        image_src = 'https:' + image_src
                    elif image_src.startswith('/'):
                        image_src = 'https://xxxx.com' + image_src
                    logging.info(f"First image source found: {image_src}")
                    return image_src

            logging.error("Failed to extract the image source from the image page.")
            return None

        except Exception as e:
            logging.error(f"Error occurred while fetching the image page: {e}")
            return None
