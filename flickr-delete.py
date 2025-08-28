import flickrapi

# Flickr API keys
API_KEY = ""
API_SECRET = ""

# Authenticate
flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET, format='parsed-json')
flickr.authenticate_via_browser(perms='delete')  # needs delete permissions

def delete_develops_albums():
    albums = flickr.photosets.getList()['photosets']['photoset']

    # Filter albums starting with the album name key
    develop_albums = [a for a in albums if a['title']['_content'].startswith(album_name_key)]

    if not develop_albums:
        print("No albums starting with 'Develops' found.")
        return

    print("The following albums will be deleted along with all their photos:")
    for album in develop_albums:
        print(f" - {album['title']['_content']} (ID: {album['id']})")

    confirm = input("Proceed with deletion? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Deletion canceled by user.")
        return

    for album in develop_albums:
        album_id = album['id']
        album_title = album['title']['_content']

        # Get all photos in the album
        photos = flickr.photosets.getPhotos(photoset_id=album_id)['photoset']['photo']

        # Delete each photo
        print(f"Deleting from album: {album_title}")
        num_photos = 0
        for photo in photos:
            photo_id = photo['id']
            flickr.photos.delete(photo_id=photo_id)
            num_photos += 1
            # print(f"Deleted photo {photo_id} from album {album_title}")
            print('.', end='', flush=True)

        print("")
        print(f"+ Deleted {num_photos} photos")
        # Delete the album
        flickr.photosets.delete(photoset_id=album_id)
        print(f"+ Deleted album {album_title}")

if __name__ == "__main__":
    album_name_key = "Develops"
    delete_develops_albums()
