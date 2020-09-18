import discord
from discord.ext import commands


class Help(commands.Cog):
    bot = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        embed.add_field(name="`>whoami`", value="Sends back data about you!")
        embed.add_field(name="`>whois <name>`", value="Sends you data about a specified user.")
        embed.add_field(name="`>ping`", value="Check to see if Xylo is responsive.")
        embed.add_field(name="`>autoreactions`", value="Check what Xylo will automatically react to!")
        await ctx.send(embed=embed, delete_after=60)


def setup(bot):
    bot.add_cog(Help(bot=bot))
