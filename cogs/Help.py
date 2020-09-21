import discord
from discord.ext import commands
from util.DiscordUtil import *


class Help(commands.Cog):
    bot = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx: commands.Context):
        """
        Check to see if the bot is responsive.
        """
        await ctx.send("Pong!")

    @commands.command("help")
    async def help(self, ctx: commands.Context):
        """
        Help command for Xylo!
        """
        await ctx.message.delete()
        embed = discord.Embed(
            title="Xylo Help",
            description="All of the commands for Xylo!",
            colour=discord.Colour.blue()
        )
        if ctx.guild is get_guild("rivertron", self.bot):
            embed.add_field(name="`>whoami`", value="Sends back data about you!")
            embed.add_field(name="`>whois <name>`", value="Sends you data about a specified user.")
        embed.add_field(name="`>ping`", value="Check to see if Xylo is responsive.")
        embed.add_field(name="`>autoreactions`", value="Check what Xylo will automatically react to!")
        await ctx.send(embed=embed, delete_after=60)


def setup(bot):
    bot.add_cog(Help(bot=bot))
