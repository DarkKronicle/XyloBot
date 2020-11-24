import requests
from scrython.foundation import FoundationObject, ScryfallError


class Deck(FoundationObject):

    def __init__(self, deck_id):
        self.url = 'decks/' + deck_id + "/export/json"
        super(Deck, self).__init__(self.url)

    async def request_data(self):
        self.scryfallJson = requests.get(self._url).json()
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
