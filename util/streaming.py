import os
import requests

TWITCH_URL = "https://api.twitch.tv/helix/search/channels?query={}"

token = os.getenv('TWITCH_TOKEN')


async def check_twitch_online(channel_name):
    headers = {"client-id": token, "Authorization": "Bearer 2gbdx6oar67tqtcmt49t3wpcgycthx"}
    r = requests.get(url=TWITCH_URL.format(channel_name), headers=headers)
    data = r.json()["data"]
    if "is_live" not in data or not data["is_live"]:
        return None
    return data
