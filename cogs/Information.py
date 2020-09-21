import discord
from util.DiscordUtil import *
from discord.ext import commands
from discord.ext.commands import Bot


class Information(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="github", aliases=["repo", "repository"])
    async def github(self, ctx: commands.Context):
        git = discord.Embed(
            title="GitHub",
            description="Go check me out on https://github.com/DarkKronicle/XyloBot",
            colour=discord.Colour.blue()
        )
        await ctx.send(embed=git)


def setup(bot):
    bot.add_cog(bot=Information(bot))
