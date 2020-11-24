import aiohttp
from scrython.foundation import FoundationObject, ScryfallError


class Deck(FoundationObject):

    def __init__(self, deck_id):
        self.url = 'decks/' + deck_id
        super(Deck, self).__init__(self.url)

    async def get_request(self, client, url, **kwargs):
        async with client.get(url, **kwargs) as response:
            return await response.json()

    async def request_data(self, *, loop=None):
        async with aiohttp.ClientSession(loop=loop) as client:
            self.scryfallJson = await self.get_request(client, self._url)
        if self.scryfallJson['object'] == 'error':
            raise ScryfallError(self.scryfallJson, self.scryfallJson['details'])
