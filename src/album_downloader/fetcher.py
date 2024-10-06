import logging
import requests
from PIL import Image
import os
from io import BytesIO

class ImageFetcher:
    def __init__(self):
        pass

    def fetch_image(self, url, save_path):
        try:
            # Attempt to download the image
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Get the content type of the file (e.g., 'image/jpeg', 'image/webp')
            content_type = response.headers.get('Content-Type', '')
            logging.info(f"Content-Type for {url}: {content_type}")

            # Check if the content type is 'image/webp'
            if 'image/webp' in content_type:
                # Convert the image to jpg format
                image = Image.open(BytesIO(response.content))
                save_path_jpg = os.path.splitext(save_path)[0] + '.jpg'  # Ensure the file is saved as .jpg
                image = image.convert('RGB')  # Convert to RGB to save as jpg
                image.save(save_path_jpg, 'JPEG')
                logging.info(f"Converted and saved WebP image as JPEG to {save_path_jpg}")
            else:
                # If it's not a WebP image, save the file as is
                save_path_jpg = os.path.splitext(save_path)[0] + '.jpg'  # Ensure we save all files as .jpg
                with open(save_path_jpg, 'wb') as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                logging.info(f"Image saved as JPEG to {save_path_jpg}")

            return True  # Return True if the image was successfully downloaded

        except requests.RequestException as e:
            logging.error(f"Failed to download image from {url}: {e}")
            return False  # Return False if there was an error
        except IOError as e:
            logging.error(f"Failed to convert or save image: {e}")
            return False
