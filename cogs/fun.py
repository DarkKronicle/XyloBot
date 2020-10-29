import random

from discord.ext import commands

from util.discord_util import *
from storage.config import *


class Fun(commands.Cog, name="Fun"):
    """
    Fun commands for Xylo. These each may be disabled by staff.
    """

    @commands.group(name="lober", invoke_without_command=True)
    async def lober(self, ctx: commands.Context):
        """
        Lober command. Send's lober information for
        """
        await ctx.send_help('lober')

    @lober.command(name="fact")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def fact(self, ctx: commands.Context):
        """
        Sends a lober fact
        """
        rand = random.choice(ConfigData.lober.data["facts"])
        embed = discord.Embed(
            title="**LOBER FACT**",
            description=rand,
            colour=discord.Colour.dark_gray()
        )
        await ctx.send(embed=embed)

    @lober.command(name="image")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image(self, ctx: commands.Context):
        """
        Sends a lober image.
        """
        lobers = await get_file_from_image(
            "https://media.discordapp.net/attachments/757781442674688041/759604260110598144/i64khd2lbns41.png?width=693&height=687",
            "lober.png")
        await ctx.send(content="**LOBER MOMENT**", file=lobers)


def setup(bot):
    bot.add_cog(Fun())
