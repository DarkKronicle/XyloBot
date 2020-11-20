import asyncio

import discord
from discord.ext import commands
from scrython.cards.cards_object import CardsObject

from util import queue
from util.context import Context
from util.paginator import SimplePages, Pages, SimplePageSource
import scrython


class CardEntry:
    def __init__(self, entry):
        self.name = entry.name
        self.id = entry.multiverse_id

    def __str__(self):
        return f"{self.name} (ID: {self.id})"


class CardEntrySource(SimplePageSource):

    async def format_page(self, menu, entries):
        await super().format_page(menu, entries)
        menu.embed.description = menu.embed.description + "\n\n*To view more information run the command `x>mtg image <ID>`*"
        return menu.embed


class CardPages(Pages):

    def __init__(self, entries, *, per_page=15):
        converted = [CardEntry(entry) for entry in entries]
        super().__init__(CardEntrySource(converted, per_page=per_page))
        self.embed = discord.Embed(colour=discord.Colour.dark_green())


class CardPages(SimplePages):

    def __init__(self, entries, *, per_page=15):
        converted = [CardEntry(entry) for entry in entries]
        super().__init__(converted, per_page=per_page)


class MagicCard(commands.Converter):

    def __init__(self, queue):
        self.queue = queue

    async def convert(self, ctx: Context, argument):
        async with queue.QueueProcess(self.queue):
            try:
                card = scrython.cards.Named(fuzzy=argument)
                await card.request_data(loop=ctx.bot.loop)
            except scrython.foundation.ScryfallError as e:
                await asyncio.sleep(0.1)
                auto = scrython.cards.Autocomplete(q=argument)
                await auto.request_data(loop=ctx.bot.loop)
                searches = auto.data()
                if len(searches) > 10:
                    searches = searches[:10]
                raise commands.BadArgument(e.error_details['details'] + f"Did you mean:\n" + "\n".join(searches))
        return card


def append_exists(message, **kwargs):
    for k, v in kwargs.items():
        if isinstance(v, tuple):
            m = v[0]
            suffix = v[1]
        else:
            m = v
            suffix = ""
        if m is None:
            continue
        message = message + f"**{k}:** {m}{suffix}\n"
    return message


def color_from_card(card):
    if card.colors() is None:
        return discord.Colour.light_gray()
    try:
        color = card.colors()[0]
    except IndexError:
        color = card.color_identity
    if color == "W":
        return discord.Colour.lighter_gray()
    if color == "U":
        return discord.Colour.blue()
    if color == "R":
        return discord.Colour.red()
    if color == "B":
        return discord.Colour.darker_grey()
    if color == "G":
        return discord.Colour.green()
    return discord.Colour.dark_grey()


def card_embed(card: CardsObject):
    description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=(card.prices("usd"), "$"))
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_image(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


class Magic(commands.Cog):
    """
    Using Scryfall API for MTG cards.
    """

    def __init__(self, bot):
        self.queue = queue.SimpleQueue(bot, 0.5)
        self.bot = bot

    @commands.group(name="mtg", aliases=["magic", "m"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def mtg(self, ctx: Context):
        """
        Magic the Gathering commands
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('mtg')

    @mtg.command(name="image", aliases=["i"])
    async def image_card(self, ctx: Context, *, card=None):
        """
        Gets a card based off of it's name.
        """
        card = await MagicCard(queue=self.queue).convert(ctx, card)
        if card is None:
            return await ctx.send_help('mtg image')
        await ctx.send(embed=card_embed(card))

    @mtg.command(name="random")
    async def image_card(self, ctx: Context):
        """
        Gets a card based off of it's name.
        """
        async with queue.QueueProcess(queue=self.queue):
            card = scrython.cards.Random()
            await card.request_data(loop=ctx.bot.loop)

        await ctx.send(embed=card_embed(card))


def setup(bot):
    bot.add_cog(Magic(bot))
