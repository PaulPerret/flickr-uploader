import flickrapi
import re
import webbrowser
import argparse

# Replace with your API key/secret
API_KEY = ""
API_SECRET = ""

PREFIX = "RT"  # albums starting with this

# Authenticate
flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format="parsed-json")
flickr.authenticate_via_browser(perms="write")

def extract_new_title(description):
    """Extract the correct album title from the description, looking for the known path."""
    description = description.replace("&quot;", '"')
    # Look for 'F:\My Pictures\Flickr Upload\' anywhere in the string
    match = re.search(r'F:\\My Pictures\\Flickr Upload\\([^\\]+)\\', description)
    if match:
        return match.group(1)
    return None

def rename_albums(dry_run=False):
    albums = flickr.photosets.getList()['photosets']['photoset']
    rename_operations = []
    skipped_albums = []

    # Collect all albums that need renaming
    for album in albums:
        title = album['title']['_content']
        if not title.startswith(PREFIX):
            continue

        description = album['description']['_content']
        new_title = extract_new_title(description)

        if new_title and new_title != title:
            rename_operations.append((album['id'], title, new_title))
        else:
            skipped_albums.append(title)

    # Dry-run output
    if rename_operations:
        print("The following albums would be renamed:")
        for _, old_title, new_title in rename_operations:
            print(f" - '{old_title}' -> '{new_title}'")
    else:
        print("No albums need renaming.")

    if skipped_albums:
        print("\nAlbums skipped (description did not contain expected path):")
        for title in skipped_albums:
            print(f" - {title}")

    if dry_run:
        print("\nDry-run mode: no changes have been made.")
        return

    if not rename_operations:
        return  # nothing to rename

    confirm = input("\nProceed with renaming these albums? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation canceled by user.")
        return

    # Perform actual renaming
    for album_id, old_title, new_title in rename_operations:
        flickr.photosets.editMeta(photoset_id=album_id, title=new_title)
        print(f"Renamed '{old_title}' -> '{new_title}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename Flickr albums based on description pattern.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without renaming albums")
    args = parser.parse_args()

    rename_albums(dry_run=args.dry_run)
