import os
import flickrapi
import argparse
import time

# Flickr API keys (replace with yours from https://www.flickr.com/services/apps/create/)
API_KEY = ""
API_SECRET = ""

# Name of the token cache file
TOKEN_CACHE_FILE = "flickr_token"
DEVELOPS_NAMES = ["LR Export", "LR Develops", "Develops", "converted"]

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

def which_subdir(parent_dir):
    for develops_dir in DEVELOPS_NAMES:
        target_path = os.path.join(parent_dir, develops_dir)
        if os.path.isdir(target_path):
            return develops_dir
    return False

def upload_albums(root_path, start_album, end_album, dry_run=False):
    develops = {}
    no_develops = []

    # Start at root_path
    all_dirs = sorted([d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))])

    # Get all directories that are between start_album and end_album
    dirs_in_range = [d for d in all_dirs if start_album <= d <= end_album]
    print("All directories in range:")
    for d in dirs_in_range:
        print(f"  {d}")

    # For each of those, check if it has a develops subdirectory
    for album in dirs_in_range:
        album_path = os.path.join(root_path, album)
        subdir_name = which_subdir(album_path)
        
        # If it does, add it to the develops list
        if subdir_name:
            develops[album_path] = subdir_name
            
        # If not, add it to the no-develops list
        else:
            no_develops.append(album_path)

    # Print out each list
    print("\nAlbums with develops:")
    for d in develops:
        print(f"  {d}\\{develops[d]}")
    print("\nAlbums without develops:")
    for d in no_develops:
        print(f"  {d}")

    # Prompt asking if want to upload no_develops list
    choice = input("\nUpload albums without develops too? (y/N): ").strip().lower()
    upload_no_develops = (choice == "y")

    # For each in develops list, upload
    for d in develops:
        print(f"[UPLOAD] Uploading album with develops: {d}")
        # TODO: call upload logic here with directory and develops subdir
        upload_directory(d, subdir_name=develops[d], dry_run=dry_run)

    # If want to upload no_develops
    for d in no_develops:
        print(f"[UPLOAD] Uploading album without develops: {d}")
        upload_directory(d, dry_run=dry_run)


def upload_directory(dirpath, subdir_name=False, dry_run=True):
    print(f"Uploading {dirpath} with subdir {subdir_name}")
    album_name = os.path.basename(dirpath)
    albums = flickr.photosets.getList(format='parsed-json')['photosets']['photoset']
    if any(album['title']['_content'] == album_name for album in albums):
        print(f"Skipping {album_name}, album already exists on Flickr.")
        return

    if (subdir_name):
        dirpath = os.path.join(dirpath, subdir_name)

    print(f"Directory to upload: {dirpath}")
    # Sort photos by filename
    files = sorted(
        [f for f in os.listdir(dirpath) if f.lower().endswith((".jpg", ".jpeg"))]
    )

    if not files:
        print(f"No photos found in {dirpath}")
    else:
        first_file = files[0]
        filepath = os.path.join(dirpath, first_file)

        if dry_run:
            print(f"[Dry-run] Would upload first photo: {filepath}")
            first_photo_id = f"dryrun_{first_file}"
            print(f"[Dry-run] Would create album '{album_name}' with first photo")
            album_id = f"dryrun_album_{album_name}"
        else:
            print(f"{first_file}, ", end="", flush=True)
            first_photo_id = upload_photo(filepath, first_file)
            album_id = get_or_create_album(album_name, first_photo_id)

        # Now upload the rest and add them to the album as we go
        for file in files[1:]:
            filepath = os.path.join(dirpath, file)
            if dry_run:
                print(f"[Dry-run] Would upload photo: {filepath} and add to album '{album_name}'")
            else:
                print(f"{file}, ", end="", flush=True)
                photo_id = upload_photo(filepath, file)
                try:
                    flickr.photosets.addPhoto(
                        format="parsed-json", photoset_id=album_id, photo_id=photo_id
                    )
                except Exception as e:
                    # Ignore if photo already exists in album
                    if "Photo already in set" not in str(e):
                        print(f"Error adding {file} to album: {e}")

        print(f"Finished uploading {len(files)} photos to album: {album_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload LR Export photos to Flickr.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded without touching Flickr")
    args = parser.parse_args()

    root_folder = "F:\\My Pictures"
    start_album = input("Enter starting album name: ").strip()
    end_album = input("Enter ending album name: ").strip()
    
    if not(start_album) or not(end_album):
        print("Start or End album missing")
    else:
        authenticate_write()
        user = flickr.test.login(format='parsed-json')
        print("Authenticated as:", user['user']['username']['_content'])
        #upload_directory(root_folder, start_album, end_album, dry_run=args.dry_run)
        upload_albums(root_folder, start_album, end_album, dry_run=args.dry_run)

