import asyncio

import discord
from discord.ext import commands, menus

from util import queue
from util.context import Context
from util.mtg_pages import CardSearch
import scrython
from scrython.cards.cards_object import CardsObject


class Searched(CardsObject):

    def __init__(self, json, **kwargs):
        super().__init__(_url="", **kwargs)
        self.scryfallJson = json


class MagicCard(commands.Converter):

    def __init__(self, queue):
        self.queue = queue

    async def convert(self, ctx: Context, argument):
        async with ctx.typing():
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
                    if len(searches) == 0:
                        extra = ". Maybe use the search command to view other cards."
                    else:
                        extra = ". Did you mean:\n" + "\n".join(searches)
                    raise commands.BadArgument(e.error_details['details'] + extra)
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
    try:
        if card.colors() is None:
            return discord.Colour.light_gray()
        try:
            color = card.colors()[0]
        except IndexError:
            color = card.colors()
    except KeyError:
        return discord.Colour.light_grey()
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


def card_image_embed(card: CardsObject):
    description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=(card.prices("usd"), "$"))
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name(), url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_image(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


def card_text_embed(card: CardsObject):
    # https://github.com/NandaScott/Scrython/blob/master/examples/get_and_format_card.py
    if card.type_line() == 'Creature':
        pt = "({}/{})".format(card.power(), card.toughness())
    else:
        pt = ""

    if card.cmc() == 0:
        mana_cost = ""
    else:
        mana_cost = card.mana_cost()

    description = """
    {cardname} {mana_cost}
    {type_line} -- {set_code} 
    {oracle_text} {power_toughness}
    *{rarity}*
    """.format(
        cardname=card.name(),
        mana_cost=mana_cost,
        type_line=card.type_line(),
        set_code=card.set_name(),
        rarity=card.rarity(),
        oracle_text=card.oracle_text(),
        power_toughness=pt
    ).replace("    ", "")
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name(), url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_thumbnail(url=str(url))
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
        if card is None:
            return await ctx.send_help('mtg image')
        card = await MagicCard(queue=self.queue).convert(ctx, card)
        if card is None:
            return await ctx.send_help('mtg image')
        await ctx.send(embed=card_image_embed(card))

    @mtg.command(name="random")
    async def random(self, ctx: Context):
        """
        Gets a card based off of it's name.
        """
        async with ctx.typing():
            async with queue.QueueProcess(queue=self.queue):
                card = scrython.cards.Random()
                await card.request_data(loop=ctx.bot.loop)

        await ctx.send(embed=card_image_embed(card))

    @mtg.command(name="search")
    async def search(self, ctx: Context, *, card=None):
        """
        Search for cards. Use https://scryfall.com/docs/syntax for complex formatting.
        """
        if card is None:
            return await ctx.send_help('mtg image')
        async with ctx.typing():
            async with queue.QueueProcess(queue=self.queue):
                try:
                    cards = scrython.cards.Search(q=card)
                    await cards.request_data()
                except scrython.foundation.ScryfallError as e:
                    return await ctx.send(e.error_details["details"])
        if len(cards.data()) == 0:
            return await ctx.send("No cards with that name found.")
        try:
            p = CardSearch([Searched(c) for c in cards.data()], card)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)
            return


def setup(bot):
    bot.add_cog(Magic(bot))
