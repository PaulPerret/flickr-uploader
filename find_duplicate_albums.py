import flickrapi
import re
import argparse

# Replace with your API key/secret
API_KEY = "c493447f40149f72909e969c968f897e"
API_SECRET = "fa4677c1c8c8ceed"

# Authenticate
flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format="parsed-json")
flickr.authenticate_via_browser(perms="read")  # read-only access is enough

def get_all_albums():
    albums = []
    page = 1
    while True:
        rsp = flickr.photosets.getList(format='parsed-json', per_page=500, page=page)
        albums.extend(rsp['photosets']['photoset'])
        if page >= rsp['photosets']['pages']:
            break
        page += 1
    return albums

def find_duplicates():
    albums = get_all_albums()
    #print(f"Albums: {albums}")
    seen = set()
    duplicate_titles = set()
    duplicate_albums = []

    for album in albums:
        title = album['title']['_content']
        if title not in seen:
            seen.add(title)
        else:
            duplicate_titles.add(title)
            
    for title in duplicate_titles:
        for album in albums:
            if album['title']['_content'] == title:
                duplicate_albums.append(album)

    return sorted(duplicate_albums, key=lambda album: album['title']['_content'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find Flickr albums not starting with an 8-digit date string.")
    args = parser.parse_args()

    albums = find_duplicates()
    print("Duplicates:")
    for album in albums:
        print(f"{album['title']['_content']},{album['photos']},{album['id']}")

