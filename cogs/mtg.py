import discord
from mtgsdk import Card
from discord.ext import commands, menus

from util import discord_util
from util.context import Context
from util.paginator import SimplePages, Pages, SimplePageSource


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

    async def convert(self, ctx: Context, argument):
        isint = False
        id = 0
        try:
            id = int(argument)
            isint = True
        except ValueError:
            pass
        if isint:
            async with ctx.typing():
                card = Card.where(multiverseid=id).where(page=1).where(pageSize=1).all()
            if card is None or len(card) == 0:
                raise commands.BadArgument("No cards found by that ID!")
            return card[0]

        async with ctx.typing():
            cards = Card.where(name=argument).where(page=1).where(pageSize=30).all()
            # Breaks if ID's are none. So just getting rid of them for now.
            for c in cards.copy():
                if c.multiverse_id is None:
                    cards.remove(c)

        if cards is None or len(cards) == 0:
            raise commands.BadArgument("No cards found with that name.")
        if len(cards) == 1:
            return cards[0]
        try:
            p = CardPages(entries=cards)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)
            return

        answer = await ctx.ask("There were multiple results that were returned. Send the number of what you want here.")
        try:
            await p.stop()
            # await p.message.delete()
        except (menus.MenuError, discord.HTTPException, TypeError):
            try:
                # Lets try to delete the message again...
                await p.message.delete()
            except (menus.MenuError, discord.HTTPException, TypeError):
                pass
            pass
        if answer is None:
            return None
        try:
            answer = int(answer)
            if answer < 1 or answer > len(p.entries):
                raise commands.BadArgument("That was too big/too small.")
            card = cards[answer - 1]
            return card
        except ValueError:
            raise commands.BadArgument("You need to specify a correct number.")


def append_exists(message, **kwargs):
    for k, v in kwargs.items():
        if v is None:
            continue
        message = message + f"**{k}:** {v}\n"
    return message


def color_from_card(card):
    if card.color_identity is None:
        return discord.Colour.light_gray()
    try:
        color = card.color_identity[0]
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
    Experimental module for MTG
    """

    @commands.group(name="mtg", aliases=["magic", "m"])
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
        card: Card
        if card.legalities is not None:
            try:
                legal = card.legalities[0]
            except IndexError:
                legal = card.legalities
        else:
            legal = {"format": None, "legality": None}
        description = append_exists("", Set=card.set_name, CMC=round(card.cmc), Format=legal["format"],
                                    Legality=legal["legality"], Rarity=card.rarity, ID=card.id)
        embed = discord.Embed(
            description=description,
            colour=color_from_card(card)
        )
        embed.set_author(name=card.name)
        if card.image_url is not None:
            embed.set_image(url=card.image_url)
        if card.release_date is not None:
            embed.set_footer(text=card.release_date)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Magic())
