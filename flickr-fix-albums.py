import argparse
import json
import os
import flickrapi

# Replace with your app keys
API_KEY = ""
API_SECRET = ""

def get_user_id(flickr):
    """Get the authenticated user's Flickr NSID."""
    rsp = flickr.test.login(format="parsed-json")
    return rsp["user"]["id"]

def get_album_by_title(flickr, user_id, title):
    """Find Flickr album (photoset) by its title."""
    rsp = flickr.photosets.getList(user_id=user_id, format="parsed-json")
    for ps in rsp['photosets']['photoset']:
        if ps['title']['_content'] == title:
            return ps
    return None

def get_photo_album(flickr, photo_id):
    """Return the album/photoset a photo belongs to, or None if not in one."""
    rsp = flickr.photos.getAllContexts(photo_id=photo_id, format="parsed-json")
    if "photoset" in rsp:
        return rsp["photoset"]["id"]
    return None

def assign_photos(flickr, user_id, json_file, dry_run=True):
    """Assign photos from JSON file to the albums by title."""
    with open(json_file, "r") as f:
        albums = json.load(f)

    for album in albums:
        title = album["title"]
        photos = album["photos"]

        flickr_album = get_album_by_title(flickr, user_id, title)
        if not flickr_album:
            print(f"[SKIP] Album '{title}' does not exist on Flickr")
            continue

        album_id = flickr_album["id"]

        for photo_id in photos:
            existing_album = get_photo_album(flickr, photo_id)
            if existing_album:
                print(f"[SKIP] Photo {photo_id} already in album {existing_album}")
                continue

            print(f"[ASSIGN] Adding photo {photo_id} to album '{title}'")
            if not dry_run:
                
                
                try:
                    flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
                    print(f"[ADD] Photo {photo_id} added to album {album_id}")
                except Exception as e:
                    msg = str(e).lower()
                    if "already in set" in msg:
                        print(f"[SKIP] Photo {photo_id} already in album {album_id}")
                        # ignore this error
                    else:
                        print(f"[ERROR] Could not add photo {photo_id} to album {album_id}: {e}")
                
                
                
                #flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)

def main():
    parser = argparse.ArgumentParser(description="Assign photos to Flickr albums from JSON mapping.")
    parser.add_argument("json_file", help="JSON file containing album/photo mapping")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    args = parser.parse_args()

    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format="parsed-json")

    # Authenticate if needed
    if not flickr.token_valid(perms="write"):
        flickr.get_request_token(oauth_callback="oob")
        authorize_url = flickr.auth_url(perms="write")
        print(f"Open this URL in browser to authorize: {authorize_url}")
        verifier = input("Verifier code: ")
        flickr.get_access_token(verifier)

    # Get the logged-in user's NSID
    user_id = get_user_id(flickr)

    # Process albums/photos
    assign_photos(flickr, user_id, args.json_file, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
