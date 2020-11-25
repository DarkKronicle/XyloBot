import asyncio

import re
from discord.ext import commands, menus

from util import queue
from util.context import Context
from util.mtg_deck import Deck
import util.mtg_pages as mp
import scrython
from scrython.cards.cards_object import CardsObject


class Searched(CardsObject):

    def __init__(self, json, **kwargs):
        super().__init__(_url="", **kwargs)
        self.scryfallJson = json


class MagicCard(commands.Converter):

    def __init__(self, queue, *, raise_again=True):
        self.queue = queue
        self.raise_again = raise_again

    async def convert(self, ctx: Context, argument):
        async with ctx.typing():
            async with queue.QueueProcess(self.queue):
                try:
                    card = scrython.cards.Named(fuzzy=argument)
                    await card.request_data(loop=ctx.bot.loop)
                except scrython.foundation.ScryfallError as e:
                    if self.raise_again:
                        raise e
                    await asyncio.sleep(0.1)
                    auto = scrython.cards.Autocomplete(q=argument)
                    await auto.request_data(loop=ctx.bot.loop)
                    searches = auto.data()
                    if len(searches) > 10:
                        searches = searches[:10]
                    if len(searches) == 0:
                        extra = ". Maybe use the search command to view other cards."
                    else:
                        extra = ". Did you mean:\n" + "\n".join(searches)
                    raise commands.BadArgument(e.error_details['details'] + extra)
        return card


class ScryfallDeck(commands.Converter):

    async def convert(self, ctx: Context, argument):
        # The following regex is to just get the url. Not parse for the ID or anything.
        if not argument.endswith("/"):
            argument = argument + "/"
        regex = r"^(https:\/\/scryfall.com\/@([^/]+)\/decks\/)([a-z0-9-]+)\/"
        pattern = re.compile(regex)
        match = pattern.match(argument)
        if not match:
            raise commands.BadArgument("URL not supported")
        # We got the URL!
        url = match.group(0)
        uuid = url.split("/")[-2]
        return Deck(uuid)


class Magic(commands.Cog):
    """
    Using Scryfall API for MTG cards.
    """

    def __init__(self, bot):
        self.queue = queue.SimpleQueue(bot, 0.5)
        self.bot = bot

    @classmethod
    async def card_page(cls, ctx, card):
        try:
            p = mp.SingleCardMenu(card)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)
            return

    async def trigger_search(self, ctx, query):
        async with ctx.typing():
            async with queue.QueueProcess(queue=self.queue):
                try:
                    cards = scrython.cards.Search(q=query)
                    await cards.request_data()
                except scrython.foundation.ScryfallError as e:
                    return await ctx.send(e.error_details["details"])
        if len(cards.data()) == 0:
            return await ctx.send("No cards with that name found.")
        try:
            p = mp.CardSearch([Searched(c) for c in cards.data()], query)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)
            return

    @commands.group(name="mtg", aliases=["magic", "m"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def mtg(self, ctx: Context):
        """
        Magic the Gathering commands
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('mtg')

    @mtg.command(name="card", aliases=["c"])
    async def image_card(self, ctx: Context, *, card=None):
        """
        Gets a card based off of it's name.
        """
        if card is None:
            return await ctx.send_help('mtg c')
        try:
            card = await MagicCard(queue=self.queue).convert(ctx, card)
            if card is None:
                return await ctx.send_help('mtg c')
            await self.card_page(ctx, card)
        except scrython.foundation.ScryfallError:
            await self.trigger_search(ctx, card)

    @mtg.command(name="collectors", aliases=["cr"])
    async def collectors_card(self, ctx: Context, set_code: str = None, *, code: int = None):
        """
        Gets a card based off of it's collecters number.
        """
        if code is None:
            return await ctx.send_help('mtg cr')
        if set_code is None:
            return await ctx.send_help('mtg cr')
        async with ctx.typing():
            async with queue.QueueProcess(queue=self.queue):
                try:
                    card = scrython.cards.Collector(code=code, collector_number=code)
                    await card.request_data(loop=ctx.bot.loop)
                except scrython.foundation.ScryfallError as e:
                    raise commands.BadArgument(e.error_details['details'])
        await self.card_page(ctx, card)

    @mtg.command(name="random")
    async def random(self, ctx: Context):
        """
        Gets a card based off of it's name.
        """
        async with ctx.typing():
            async with queue.QueueProcess(queue=self.queue):
                card = scrython.cards.Random()
                await card.request_data(loop=ctx.bot.loop)

        await self.card_page(ctx, card)

    @mtg.command(name="search")
    async def search(self, ctx: Context, *, card=None):
        """
        Search for cards. Use https://scryfall.com/docs/syntax for complex formatting.
        """
        if card is None:
            return await ctx.send_help('mtg image')
        await self.trigger_search(ctx, card)

    @mtg.command(name="advancedsearch", aliases=["asearch"])
    async def advanced_search(self, ctx: Context):
        """
        Search using complex parameters.
        """
        try:
            p = mp.AdvancedSearch(self.queue)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)
            return

    @mtg.command(name="deck")
    async def deck(self, ctx: Context, *, deck: ScryfallDeck = None):
        deck: Deck
        if deck is None:
            return await ctx.send_help('mtg deck')
        async with ctx.typing():
            async with queue.QueueProcess(self.queue):
                await deck.request_data()
            await ctx.send(f"Your deck count is: `{deck.count_entries()}`")


def setup(bot):
    bot.add_cog(Magic(bot))
