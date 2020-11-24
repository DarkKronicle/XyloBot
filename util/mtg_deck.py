import io
import json

import aiohttp
import requests
from scrython.foundation import FoundationObject, ScryfallError


class Deck(FoundationObject):

    def __init__(self, deck_id):
        self.url = 'decks/' + deck_id + "/export/json"
        super(Deck, self).__init__(self.url)
        self._url = 'https://api.scryfall.com/{0}'.format(self.url)

    async def get_data_from_url(self, url: str, *, loop=None):
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = io.BytesIO(await resp.read())
                return data

    async def request_data(self, *, loop=None):
        data = await self.get_data_from_url(self._url, loop=loop)
        data.seek(0)
        self.scryfallJson = json.loads(data.read())
        if self.scryfallJson['object'] == 'error':
            raise ScryfallError(self.scryfallJson, self.scryfallJson['details'])

    def count_entries(self):
        sections = self.scryfallJson["sections"]["primary"]
        try:
            sections.extend(self.scryfallJson["sections"]["secondary"])
        except IndexError:
            pass
        card_num = 0
        for section in sections:
            for card in self.scryfallJson["entries"][section]:
                if card["raw_text"] == "":
                    continue
                card_num = card_num + card["count"]

        return card_num
