from album_downloader.downloader import AlbumDownloader

if __name__ == "__main__":
    # List of album URLs for testing
    album_urls = [
        "xxxx",
        # Add more URLs as needed
    ]

    # Iterate over each album URL and process each album
    for album_url in album_urls:
        print(f"Processing album: {album_url}")

        # Initialize AlbumDownloader for each URL
        downloader = AlbumDownloader(album_url)

        # Fetch album information
        downloader.fetch_album_info()

        # Download images for the album
        downloader.download_images()

        print(f"Completed processing for album: {album_url}")
