import os
import flickrapi
import argparse
import time

# Flickr API keys (replace with yours from https://www.flickr.com/services/apps/create/)
API_KEY = ""
API_SECRET = ""

# Name of the token cache file
TOKEN_CACHE_FILE = "flickr_token"

# Single global client; use JSON for normal API calls
flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format='etree', cache=True)

def authenticate_write():
    """Ensure we have a valid write token on the single global client."""
    if not flickr.token_valid(perms='write'):
        flickr.get_request_token(oauth_callback='oob')
        authorize_url = flickr.auth_url(perms='write')
        print(f"Open this URL in a browser to authorize the app: {authorize_url}")
        verifier = input("Enter the verifier code: ")
        flickr.get_access_token(verifier)

def get_or_create_album(title, primary_photo_id=None):
    """Find an album by title or create it if it doesn't exist."""
    albums = flickr.photosets.getList(format='parsed-json')['photosets']['photoset']
    for album in albums:
        if album['title']['_content'] == title:
            return album['id']
    # Create new album if not found
    if primary_photo_id:
        new_album = flickr.photosets.create(format='parsed-json', title=title, primary_photo_id=primary_photo_id)
        album_id = new_album['photoset']['id']
        print(f"Created new album: {title} (ID: {album_id})")
        return album_id
    return None

def upload_photo(filepath, title, retries=3, backoff=2):
    """
    Upload a single photo and return the photo_id (string).
    Safely switches the client to 'etree' for upload, then restores format.
    """
    # Normalize Windows path to forward slashes for HTTPS multipart
    filepath = filepath.replace("\\", "/")

    flickr.format = 'etree'  # IMPORTANT: upload returns XML, not JSON
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            rsp = flickr.upload(filename=filepath, title=title)
            # rsp is an Element (XML). Extract <photoid>
            pid_el = rsp.find('photoid')
            if pid_el is None or not pid_el.text:
                # Dump raw XML to help debug server-side errors
                raw_xml = ET.tostring(rsp, encoding='unicode')
                raise RuntimeError(f"Upload returned no <photoid>. Response: {raw_xml}")
            return pid_el.text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff ** attempt)
            else:
                raise last_err

def upload_directory(root_path, start_album, end_album, dry_run=False):
    candidate_dirs = []
    no_develops = []

    # Collect all directories with/without a develops folder
    for dirpath, dirnames, filenames in os.walk(root_path):
        if develops_folder_name in dirnames:
            album_name = os.path.basename(dirpath)
            if start_album <= album_name <= end_album:
                develop_path = os.path.join(dirpath, develops_folder_name)
                # Count photos for preview
                num_photos = len([f for f in os.listdir(develop_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
                candidate_dirs.append((dirpath, num_photos))
        else:
            if start_album <= os.path.basename(dirpath) <= end_album:
                no_develops.append(dirpath)

    # Sort candidate dirs in alphabetical order by basename
    candidate_dirs.sort(key=lambda x: os.path.basename(x[0]), reverse=False)

    if not candidate_dirs:
        print("No albums found in the specified range.")
        return

    # Print albums to be uploaded with photo counts for confirmation
    print("The following albums will be uploaded:")
    for dirpath, num_photos in candidate_dirs:
        print(f" - {os.path.basename(dirpath)} ({num_photos} photos)")

    confirm = input("Proceed with upload? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Upload canceled by user.")
        return

    # Process directories
    for dirpath, _ in candidate_dirs:
        album_name = os.path.basename(dirpath)
        albums = flickr.photosets.getList(format='parsed-json')['photosets']['photoset']
        if any(album['title']['_content'] == album_name for album in albums):
            print(f"Skipping {album_name}, album already exists on Flickr.")
            continue

        develop_path = os.path.join(dirpath, develops_folder_name)

        # Sort photos by filename
        files = sorted(
            [f for f in os.listdir(develop_path) if f.lower().endswith((".jpg", ".jpeg"))]
        )

        photo_ids = []
        for file in files:
            filepath = os.path.join(develop_path, file)
            if dry_run:
                print(f"[Dry-run] Would upload photo: {filepath}")
                photo_id = f"dryrun_{file}"  # placeholder
            else:
                print(f"Uploading {filepath}")
                photo_id = upload_photo(filepath, file)
            photo_ids.append(photo_id)

        if photo_ids:
            if dry_run:
                print(f"[Dry-run] Would create album '{album_name}' and add {len(photo_ids)} photos")
            else:
                album_id = get_or_create_album(album_name, photo_ids[0])
                for pid in photo_ids[1:]:
                    flickr.photosets.addPhoto(format='parsed-json', photoset_id=album_id, photo_id=pid)
                    #print(f"Added photo {pid} to album {album_name}")
                print(f"Finished uploading {len(photo_ids)} photos to album: {album_name}")

    # Print log of missing directories (works in dry-run too)
    print(f"\nChecking for directories without '{develops_folder_name}' subfolder:")
    if no_develops:
        for d in no_develops:
            print(f" - {d}")
    else:
        print("All directories had the subfolder.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload LR Export photos to Flickr.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded without touching Flickr")
    args = parser.parse_args()

    root_folder = "F:\\My Pictures"
    develops_folder_name = "Develops"
    start_album = input("Enter starting album name: ").strip()
    end_album = input("Enter ending album name: ").strip()
    authenticate_write()
    user = flickr.test.login(format='parsed-json')
    print("Authenticated as:", user['user']['username']['_content'])
    upload_directory(root_folder, start_album, end_album, dry_run=args.dry_run)
