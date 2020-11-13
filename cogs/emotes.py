import discord
from discord.ext import commands

from util.context import Context


class Emotes(commands.Cog):
    """
    Send a fun little picture to express your opinion and mood. (All of these start with : to prevent issues)
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=":thumb")
    async def thumb(self, ctx: Context, *, extra):
        embed = discord.Embed(
            description=extra,
            colour=discord.Colour.magenta()
        )
        with open("assets/emotes/thumb.png", "r") as buffer:
            file = discord.File(fp=buffer, filename="thumb.png")
        embed.set_image(url="attachment://thumb.png")
        embed.set_author(icon_url=ctx.author.avatar_url, name=ctx.author.display_name)
        await ctx.send(embed=embed, file=file)


def setup(bot):
    bot.add_cog(Emotes(bot))
