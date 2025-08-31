import os
import argparse
import flickrapi

# Replace with your Flickr API key and secret
API_KEY = ""
API_SECRET = ""

def authenticate():
    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format='etree')

    if not flickr.token_valid(perms='write'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='write')
        print("Open this URL in your browser to authorize the app:")
        print(authorize_url)
        verifier = input("Verifier code: ")
        flickr.get_access_token(verifier)

    return flickr

def ensure_album(flickr, album_name, primary_photo_id):
    """Check if album exists, else create it."""
    rsp = flickr.photosets.getList(format='parsed-json')
    albums = rsp['photosets']['photoset']
    for album in albums:
        if album['title']['_content'] == album_name:
            return album['id']

    # Create a new album with the first uploaded photo as primary
    rsp = flickr.photosets.create(title=album_name, primary_photo_id=primary_photo_id, format='parsed-json')
    return rsp['photoset']['id']

def upload_directory(flickr, directory, album_title=None):
    # Default album title is the directory name if not provided
    album_name = album_title if album_title else os.path.basename(os.path.normpath(directory))
    uploaded_photo_ids = []

    print(f"Uploading directory: {directory} to album: {album_name}")

    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)
        if not os.path.isfile(filepath):
            continue
        if not file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        print(f"{file}, ", end='', flush=True)
        rsp = flickr.upload(filename=filepath, title=file)
        photo_id = rsp.find('photoid').text
        uploaded_photo_ids.append(photo_id)

    if not uploaded_photo_ids:
        print("No photos uploaded, nothing to do.")
        return

    # Ensure album exists (create if missing)
    album_id = ensure_album(flickr, album_name, uploaded_photo_ids[0])

    # Add remaining photos to album
    for pid in uploaded_photo_ids[1:]:
        flickr.photosets.addPhoto(photoset_id=album_id, photo_id=pid)
    print(f"\nAdded photos to album {album_name}")

def main():
    parser = argparse.ArgumentParser(description="Upload a directory of photos to Flickr.")
    parser.add_argument("directory", help="Path to directory with photos")
    parser.add_argument("--title", help="Optional album title to use on Flickr (defaults to directory name)")
    args = parser.parse_args()

    flickr = authenticate()
    upload_directory(flickr, args.directory, args.title)

if __name__ == "__main__":
    main()
