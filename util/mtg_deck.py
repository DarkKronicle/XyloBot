import io
import json

import aiohttp
from scrython.foundation import FoundationObject, ScryfallError


class URLDeck(FoundationObject):
    """
    A class just to request data from Scryfall. Deck gives all the info in a nicely accessible format.
    """

    def __init__(self, deck_id):
        self.url = 'decks/' + deck_id + "/export/json"
        super().__init__(self.url)
        self._url = 'https://api.scryfall.com/{0}'.format(self.url)

    async def get_request(self, url: str, *, loop=None):
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = io.BytesIO(await resp.read())
                return data

    async def request_data(self, *, loop=None):
        data = await self.get_request(self._url, loop=loop)
        data.seek(0)
        self.scryfallJson = json.loads(data.read())
        if self.scryfallJson['object'] == 'error':
            raise ScryfallError(self.scryfallJson, self.scryfallJson['details'])
        return Deck(self.scryfallJson)


class DeckCard:
    __slots__ = ("section", "raw_text", "count", "name", "image", "url", "mana", "type_line", "found")

    def __init__(self, data: dict):
        self.section = data.get("section")
        self.raw_text = data.get("raw_text")
        self.count = data.get("count")
        self.found = data.get("found")
        digest = data.get("card_digest", {})
        if digest is None:
            digest = {}
        self.image = digest.get("image")
        self.url = digest.get("scryfall_uri")
        self.type_line = digest.get("type_line")
        self.mana = digest.get("mana_cost")
        self.name = digest.get("name")


class Deck:
    """
    A class to keep track of deck data.

    Decks can be pretty complex, this will help arrange them and provide helpful utilities.
    """

    def __init__(self, data):
        self.id = data.get("id")
        self.url = data.get("uri")
        self.name = data.get("name")
        self.description = data.get("description")
        self.primary_sections = data.get("sections", {}).get("primary", [])
        self.secondary_sections = data.get("sections", {}).get("secondary", [])
        self.all_sections = self.primary_sections + self.secondary_sections
        self.cards = []
        for section in self.all_sections:
            for card in data.get("entries", {}).get(section):
                c = DeckCard(card)
                if c.raw_text != "":
                    self.cards.append(c)

    def count_entries(self):
        return len(self.cards)
