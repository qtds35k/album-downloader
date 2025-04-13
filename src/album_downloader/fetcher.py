import logging
import cloudscraper
from PIL import Image
import os
from io import BytesIO

class ImageFetcher:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def fetch_image(self, url, save_path):
        try:
            response = self.scraper.get(url, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            logging.info(f"Content-Type for {url}: {content_type}")

            if 'image/webp' in content_type:
                image = Image.open(BytesIO(response.content))
                save_path_jpg = os.path.splitext(save_path)[0] + '.jpg'
                image = image.convert('RGB')
                image.save(save_path_jpg, 'JPEG')
                logging.info(f"Converted and saved WebP image as JPEG to {save_path_jpg}")
            else:
                save_path_jpg = os.path.splitext(save_path)[0] + '.jpg'
                with open(save_path_jpg, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                logging.info(f"Image saved as JPEG to {save_path_jpg}")

            return True

        except Exception as e:
            logging.error(f"Failed to download image from {url}: {e}")
            return False
