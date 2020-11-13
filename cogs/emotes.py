import discord
from discord.ext import commands

from util.context import Context


async def simple_emote(filename, ctx, description, *, embed=None):
    if embed is None:
        embed = discord.Embed(
            description=description,
            colour=discord.Colour.magenta()
        )
    with open(filename, "rb") as buffer:
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="whoputyou.png")

    embed.set_image(url="attachment://whoputyou.png")
    embed.set_author(icon_url=ctx.author.avatar_url, name=ctx.author.display_name)
    await ctx.send(embed=embed, file=file)


class Emotes(commands.Cog):
    """
    Send a fun little picture to express your opinion and mood. (All of these start with : to prevent issues)
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=":thumb")
    async def thumb(self, ctx: Context, *, extra: commands.clean_content):
        """
        Show your approval
        """
        if extra is None:
            extra = "Thumb"
        await simple_emote("assets/emotes/thumb.png", ctx, extra)

    @commands.command(name=":whoputyou")
    async def whoputyou(self, ctx: Context, *, extra: commands.clean_content):
        """
        Who put YOU on the planet
        """
        if extra is None:
            extra = "Who put you on the planet?"
        await simple_emote("assets/emotes/whoputyou.png", ctx, extra)

    @commands.command(name=":why")
    async def why(self, ctx: Context, *, extra: commands.clean_content):
        """
        Why?
        """
        if extra is None:
            extra = "Why?"
        await simple_emote("assets/emotes/why.png", ctx, extra)

    @commands.command(name=":dude")
    async def why(self, ctx: Context, *, extra: commands.clean_content):
        """
        Why?
        """
        if extra is None:
            extra = "dude"
        await simple_emote("assets/emotes/dude.png", ctx, extra)


def setup(bot):
    bot.add_cog(Emotes(bot))
