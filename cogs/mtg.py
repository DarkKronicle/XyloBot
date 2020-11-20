import discord
from mtgsdk import Card
from discord.ext import commands, menus
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

    def __init__(self, *, queue=None):
        self.queue = queue

    async def convert(self, ctx: Context, argument):
        if self.queue is None:
            card = scrython.cards.Named(fuzzy=argument)
        else:
            async with queue.QueueProcess(self.queue):
                card = scrython.cards.Named(fuzzy=argument)

        return card


def append_exists(message, **kwargs):
    for k, v in kwargs.items():
        if v is None:
            continue
        message = message + f"**{k}:** {v}\n"
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


class Magic(commands.Cog):
    """
    Using Scryfall API for MTG cards.
    """

    def __init__(self):
        self.queue = queue.SimpleQueue(0.5)

    @commands.group(name="mtg", aliases=["magic", "m"], hidden=True)
    @commands.is_owner()
    async def mtg(self, ctx: Context):
        """
        Magic the Gathering commands
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('mtg')

    @mtg.command(name="search")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def search(self, ctx: Context, *args):
        """
        Searches for a MTG card.
        """
        if len(args) == 0:
            return await ctx.send_help('m search')

        cards = Card.where(name=' '.join(args)).where(page=1).where(pageSize=50).all()

        if len(cards) == 0:
            return await ctx.send("None found")
        try:
            p = CardPages(entries=cards)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)

    @mtg.command(name="image", aliases=["i"])
    @commands.cooldown(2, 15, commands.BucketType.user)
    async def image_card(self, ctx: Context, *, card: MagicCard = None):
        """
        Gets a cards image.
        """
        if card is None:
            return await ctx.send_help('mtg image')
        card: CardsObject
        description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=card.prices("usd"))
        embed = discord.Embed(
            description=description,
            colour=color_from_card(card)
        )
        embed.set_author(name=card.name())
        url = card.image_uris(0, "png")
        if url is not None:
            embed.add_field(name="Image", value=str(url))
        # footer = ""
        # if card.multiverse_id is not None:
        #     footer = footer + f"ID: {card.multiverse_id}"
        # if card.release_date is not None:
        #     footer = footer + f"- {card.multiverse_id}"
        # if footer != "":
        #     embed.set_footer(text=footer)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Magic())
