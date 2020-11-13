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


class Emotes(commands.Cog):
    """
    Send a fun little picture to express your opinion and mood. (All of these start with : to prevent issues)
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=":thumb")
    async def thumb(self, ctx: Context, *, extra: commands.clean_content = None):
        """
        Show your approval
        """
        if extra is None:
            extra = "Thumb"
        await simple_emote("assets/emotes/thumb.png", "thumb.png", ctx, extra)

    @commands.command(name=":whoputyou")
    async def whoputyou(self, ctx: Context, *, extra: commands.clean_content = None):
        """
        Who put YOU on the planet
        """
        if extra is None:
            extra = "Who put you on the planet?"
        await simple_emote("assets/emotes/whoputyou.png", "whoputyou.png", ctx, extra)

    @commands.command(name=":why")
    async def why(self, ctx: Context, *, extra: commands.clean_content = None):
        """
        Why?
        """
        if extra is None:
            extra = "Why?"
        await simple_emote("assets/emotes/why.png", "why.png", ctx, extra)

    @commands.command(name=":dude")
    async def dude(self, ctx: Context, *, extra: commands.clean_content = None):
        """
        Dude
        """
        if extra is None:
            extra = "dude"
        await simple_emote("assets/emotes/dude.png", "dude.png", ctx, extra)

    @commands.command(name=":chill")
    async def chill(self, ctx: Context, *, extra: commands.clean_content = None):
        """
        Show your approval
        """
        if extra is None:
            extra = "Chill bruh"
        await simple_emote("assets/emotes/calm.gif", "calm.gif", ctx, extra)

    @commands.command(name=":rage")
    async def rage(self, ctx: Context, *, extra: commands.clean_content = None):
        """
        Show your approval
        """
        if extra is None:
            extra = "RAGE"
        await simple_emote("assets/emotes/rage.gif", "rage.gif", ctx, extra)


def setup(bot):
    bot.add_cog(Emotes(bot))
