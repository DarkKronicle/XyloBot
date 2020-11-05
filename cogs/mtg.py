from mtgsdk import Card
from discord.ext import commands, menus

from util import discord_util
from util.context import Context
from util.paginator import SimplePages


class CardEntry:
    def __init__(self, entry):
        self.name = entry.name
        self.id = entry.multiverse_id

    def __str__(self):
        return f"{self.name} (ID: {self.id})"


class CardPages(SimplePages):

    def __init__(self, entries, *, per_page=15):
        converted = [CardEntry(entry) for entry in entries]
        super().__init__(converted, per_page=per_page)


class Magic(commands.Cog):
    """
    Experimental module for MTG
    """

    @commands.group(name="mtg", aliases=["magic", "m"], hidden=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mtg(self, ctx: Context):
        """
        Magic the Gathering commands
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('mtg')

    @mtg.command(name="search")
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

    @mtg.command(name="id")
    async def by_id(self, ctx: Context, id: int = None):
        """
        Gets a card by ID. (Seen in the search command)
        """
        if id is None:
            return await ctx.send_help('mtg id')

        card = Card.where(multiverseid=id).where(page=1).where(pageSize=1).all()
        if card is None or len(card) == 0:
            return await ctx.send("No card by that ID found.")

        card = card[0]
        try:
            image = await discord_util.get_file_from_image(card.image.image_url, "magic.png")
        except Exception:
            return await ctx.send("Couldn't download image. Try again later.")
        if image is None:
            return await ctx.send("Couldn't download image. Try again later.")

        await ctx.send(file=image)


def setup(bot):
    bot.add_cog(Magic())
