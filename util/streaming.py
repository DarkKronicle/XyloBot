import os
import requests

TWITCH_URL = "https://api.twitch.tv/helix/search/channels?query={}"

API_HEADERS = {
    'client-id': os.getenv('TWITCH_TOKEN'),
    'Authorization': "Bearer 2gbdx6oar67tqtcmt49t3wpcgycthx"
}


async def check_twitch_online(channel_name):
    r = requests.get(url=TWITCH_URL.format(channel_name), params=API_HEADERS)
    data = r.json()["data"]
    if "is_live" not in data or not data["is_live"]:
        return None
    return data
