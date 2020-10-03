import os
import requests

TWITCH_URL = "https://api.twitch.tv/helix/search/channels?query={}"

twitch_id = os.getenv('TWITCH_ID')
twich_token = os.getenv('TWITCH_TOKEN')


async def check_twitch_online(channel_name):
    headers = {"client-id": twitch_id, "Authorization": f"Bearer {twich_token}"}
    r = requests.get(url=TWITCH_URL.format(channel_name), headers=headers)
    data = r.json()
    print(data)
    if "is_live" not in data or not data["is_live"]:
        return None
    return data
