import flickrapi
import argparse
import json
import time
import os

API_KEY = ""
API_SECRET = ""

def get_albums(flickr, prefix):
    """Fetch all albums starting with the given prefix."""
    albums = []
    page = 1
    while True:
        rsp = flickr.photosets.getList(page=page, per_page=500, format="json", nojsoncallback=1)

        # Decode JSON string into dict
        if isinstance(rsp, bytes):
            rsp = rsp.decode("utf-8")
        if isinstance(rsp, str):
            rsp = json.loads(rsp)

        for a in rsp["photosets"]["photoset"]:
            title = a["title"]["_content"]
            if title.startswith(prefix):
                albums.append({
                    "id": a["id"],
                    "title": title,
                    "description": a["description"]["_content"]
                })
        if page >= rsp["photosets"]["pages"]:
            break
        page += 1
    return sorted(albums, key=lambda x: x["title"].lower())

def get_album_photos(flickr, album_id):
    """Fetch all photo IDs in an album (handles pagination)."""
    photos = []
    page = 1
    while True:
        rsp = flickr.photosets.getPhotos(photoset_id=album_id, page=page, per_page=500, format="json", nojsoncallback=1)

        # Decode JSON string into dict
        if isinstance(rsp, bytes):
            rsp = rsp.decode("utf-8")
        if isinstance(rsp, str):
            rsp = json.loads(rsp)

        photos.extend([p["id"] for p in rsp["photoset"]["photo"]])
        if page >= rsp["photoset"]["pages"]:
            break
        page += 1
    return photos

def backup_albums(flickr, albums, backup_file):
    """Save album metadata + photo IDs to JSON file."""
    data = []
    for album in albums:
        photos = get_album_photos(flickr, album["id"])
        data.append({
            "id": album["id"],
            "title": album["title"],
            "description": album["description"],
            "photos": photos
        })
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Backup saved to {backup_file}")

def process_albums(flickr, albums, dry_run=False):
    """Delete, recreate, and re-add photos to albums in alphabetical order."""
    for idx, album in enumerate(albums, start=1):
        start_time = time.time()
        photos = get_album_photos(flickr, album["id"])
        print(f"[{idx}/{len(albums)}] Album: '{album['title']}', Photos: {len(photos)}")

        if dry_run:
            continue  # Just report, don’t change anything

        # Delete old album
        flickr.photosets.delete(photoset_id=album["id"])
        time.sleep(1)
        print(f"  Deleted old album... ", end="", flush=True)

        # Recreate album (needs a primary photo ID)
        if not photos:
            print(f"  Skipping empty album: {album['title']}")
            continue
        rsp = flickr.photosets.create(
            title=album["title"],
            description=album["description"],
            primary_photo_id=photos[0],
            format="json", nojsoncallback=1
        )

        # Decode JSON string into dict
        if isinstance(rsp, bytes):
            rsp = rsp.decode("utf-8")
        if isinstance(rsp, str):
            rsp = json.loads(rsp)

        new_album_id = rsp["photoset"]["id"]
        print(f"Created new one... ", end="", flush=True)      
        
        # Add remaining photos
        print(f"Re-adding photos... ", end="", flush=True)      
        for pid in photos[1:]:
            try:
                flickr.photosets.addPhoto(
                    photoset_id=new_album_id,
                    photo_id=pid,
                    format="json", nojsoncallback=1
                )
                time.sleep(0.2)  # be gentle with API rate limits
            except Exception as e:
                print(f"  [ERROR] Could not add photo {pid} to album {album['title']}: {e}")
        end_time = time.time()
        print(f"Done. ({round(end_time - start_time, 1)}s)")

def main():
    parser = argparse.ArgumentParser(description="Reorder Flickr albums alphabetically.")
    parser.add_argument("prefix", help="Prefix of albums to reorder")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying Flickr")
    parser.add_argument("--backup", default="albums_backup.json", help="Backup file for album metadata")
    args = parser.parse_args()

    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format="parsed-json")
    flickr.authenticate_via_browser(perms="delete")

    albums = get_albums(flickr, args.prefix)
    if not albums:
        print("No albums found with that prefix.")
        return

    print(f"Found {len(albums)} albums starting with '{args.prefix}'")
    print("Backing up albums before making changes...")
    backup_albums(flickr, albums, args.backup)

    process_albums(flickr, albums, dry_run=args.dry_run)

    print("Done.")

if __name__ == "__main__":
    main()
