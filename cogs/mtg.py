from mtgsdk import Card
from discord.ext import commands, menus

from util.context import Context
from util.paginator import SimplePages


class CardEntry:
    def __init__(self, entry):
        self.id = entry.name
        self.name = entry.id

    def __str__(self):
        return f"{self.name} (ID: {self.id})"


class CardPages(SimplePages):

    def __init__(self, entries, *, per_page=15):
        converted = [CardEntry(entry) for entry in entries]
        super().__init__(converted, per_page=per_page)


class Magic(commands.Cog, hidden=True):
    """
    Experimental module for MTG
    """

    @commands.group(name="mtg", aliases=["magic", "m"])
    async def mtg(self, ctx: Context):
        """
        Experimental
        """
        pass

    @mtg.command(name="search")
    async def search(self, ctx: Context, *args):
        if len(args) == 0:
            return await ctx.send_help('m search')

        cards = Card.where(name=' '.join(args)).where(page=1).where(pageSize=50).all()

        if len(cards) == 0:
            return await ctx.send("None found")
        try:
            p = CardPages(entries=entries)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Magic())
