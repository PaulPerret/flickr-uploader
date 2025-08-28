import flickrapi
import re
import argparse

# Replace with your API key/secret
API_KEY = "c493447f40149f72909e969c968f897e"
API_SECRET = "fa4677c1c8c8ceed"

# Authenticate
flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format="parsed-json")
flickr.authenticate_via_browser(perms="read")  # read-only access is enough

def find_non_date_albums():
    albums = flickr.photosets.getList()['photosets']['photoset']
    non_date_albums = []

    # Regex for 8-digit date at the start of the album title
    date_pattern = re.compile(r'^\d{8}')

    for album in albums:
        title = album['title']['_content']
        if not date_pattern.match(title):
            non_date_albums.append(title)

    return non_date_albums

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find Flickr albums not starting with an 8-digit date string.")
    args = parser.parse_args()

    albums = find_non_date_albums()
    if albums:
        print("Albums not starting with 8-digit date string:")
        for title in albums:
            print(f" - {title}")
    else:
        print("All albums start with an 8-digit date string.")
