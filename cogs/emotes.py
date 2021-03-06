import discord
from discord.ext import commands

from util.context import Context


async def simple_emote(filename, sendname, ctx, description, *, embed=None):
    if embed is None:
        embed = discord.Embed(
            description=description,
            colour=discord.Colour.magenta()
        )
    with open(filename, "rb") as buffer:
        buffer.seek(0)
        file = discord.File(fp=buffer, filename=sendname)

    embed.set_image(url=f"attachment://{sendname}")
    embed.set_author(icon_url=ctx.author.avatar_url, name=ctx.author.display_name)
    await ctx.send(embed=embed, file=file)
    await ctx.delete()


class Emotes(commands.Cog):
    """
    Send a fun little picture to express your opinion and mood.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=":thumb")
    async def thumb(self, ctx: Context, *, extra: commands.clean_content = None):
        """Show your approval"""
        if extra is None:
            extra = "Thumb"
        await simple_emote("assets/emotes/thumb.png", "thumb.png", ctx, extra)

    @commands.command(name=":disgust")
    async def whoputyou(self, ctx: Context, *, extra: commands.clean_content = None):
        """ Show your disgust"""
        if extra is None:
            extra = "Who put you on the planet?"
        await simple_emote("assets/emotes/whoputyou.png", "whoputyou.png", ctx, extra)

    @commands.command(name=":why")
    async def why(self, ctx: Context, *, extra: commands.clean_content = None):
        """Why?"""
        if extra is None:
            extra = "Why?"
        await simple_emote("assets/emotes/why.png", "why.png", ctx, extra)

    @commands.command(name=":dude")
    async def dude(self, ctx: Context, *, extra: commands.clean_content = None):
        """ Dude"""
        if extra is None:
            extra = "dude"
        await simple_emote("assets/emotes/dude.png", "dude.png", ctx, extra)

    @commands.command(name=":chill")
    async def chill(self, ctx: Context, *, extra: commands.clean_content = None):
        """Chill out"""
        if extra is None:
            extra = "Chill bruh"
        await simple_emote("assets/emotes/calm.gif", "calm.gif", ctx, extra)

    @commands.command(name=":rage")
    async def rage(self, ctx: Context, *, extra: commands.clean_content = None):
        """AAAAAA"""
        if extra is None:
            extra = "RAGE"
        await simple_emote("assets/emotes/rage.gif", "rage.gif", ctx, extra)

    @commands.command(name=":satan")
    async def satan(self, ctx: Context, *, extra: commands.clean_content = None):
        """LET EVERYTHING BURN"""
        if extra is None:
            extra = "BURN BURN BURN"
        await simple_emote("assets/emotes/elmosatan.gif", "elmosatan.gif", ctx, extra)

    @commands.command(name=":checkmate")
    async def checkmate(self, ctx: Context, *, extra: commands.clean_content = None):
        """Checkmate"""
        if extra is None:
            extra = "checkmate"
        await simple_emote("assets/emotes/checkmate.gif", "checkmate.gif", ctx, extra)

    @commands.command(name=":idiot")
    async def idiot(self, ctx: Context, *, extra: commands.clean_content = None):
        """You idiot"""
        if extra is None:
            extra = "You are an idiot, and you did that."
        await simple_emote("assets/emotes/idiot.gif", "idiot.gif", ctx, extra)

    @commands.command(name=":yes")
    async def yes(self, ctx: Context, *, extra: commands.clean_content = None):
        """Yes yes yes yes"""
        if extra is None:
            extra = "YES BA BA BOI"
        await simple_emote("assets/emotes/yes.gif", "yes.gif", ctx, extra)

    @commands.command(name=":no")
    async def no(self, ctx: Context, *, extra: commands.clean_content = None):
        """no"""
        if extra is None:
            extra = "no"
        await simple_emote("assets/emotes/no.gif", "no.gif", ctx, extra)

    @commands.command(name=":power")
    async def power(self, ctx: Context, *, extra: commands.clean_content = None):
        """I have the power of anime AND god on my side!"""
        if extra is None:
            extra = "I have the power"
        await simple_emote("assets/emotes/power.gif", "power.gif", ctx, extra)

    @commands.command(name=":mydudes")
    async def mydudes(self, ctx: Context, *, extra: commands.clean_content = None):
        """It do be wednesday my dudes"""
        if extra is None:
            extra = "mydudes"
        await simple_emote("assets/emotes/mydudes.gif", "mydudes.gif", ctx, extra)


def setup(bot):
    bot.add_cog(Emotes(bot))
