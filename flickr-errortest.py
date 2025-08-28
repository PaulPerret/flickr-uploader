import requests
from requests_oauthlib import OAuth1

# Replace with your keys/tokens
API_KEY = "c493447f40149f72909e969c968f897e"
API_SECRET = "fa4677c1c8c8ceed"
oauth = OAuth1(API_KEY, API_SECRET)

filepath = r"F:\My Pictures\20050117_Florida\Develops\CRW_1641.jpg"

with open(filepath, "rb") as f:
    files = {"photo": f}
    data = {"title": "example"}
    response = requests.post("https://up.flickr.com/services/upload/", files=files, data=data, auth=oauth)
    print("Status code:", response.status_code)
    print("Response text:", response.text)
