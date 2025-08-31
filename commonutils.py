

"""
Retrieves all photo albums (photosets) from a Flickr account using the provided Flickr API client.

Args:
    flickr: An authenticated Flickr API client instance.

Returns:
    list: A list of dictionaries, each representing a Flickr album (photoset).

Raises:
    Exception: If the Flickr API request fails or returns an unexpected response.

Note:
    This function paginates through all available albums, fetching up to 500 albums per page.
"""
def get_all_albums(flickr):

    albums = []
    page = 1
    while True:
        rsp = flickr.photosets.getList(format='parsed-json', per_page=500, page=page)
        albums.extend(rsp['photosets']['photoset'])
        if page >= rsp['photosets']['pages']:
            break
        page += 1
    return albums