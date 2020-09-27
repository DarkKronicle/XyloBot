import random

import discord
from discord.ext import commands
from util.DiscordUtil import *
from storage import Cache
from storage.Config import *


def lober():
    async def predicate(context: commands.Context):
        fields = Cache.get_fun(context.guild)
        if fields is not None and fields["lober"]:
            return True
        return False

    return commands.check(predicate)


class Fun(commands.Cog):

    @commands.group(name="lober")
    @commands.cooldown(2, 30, commands.BucketType.user)
    @lober()
    async def lober(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Lober Help",
                description="What lober commands I got.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`>lober fact`", value="View a random lober fact!")
            await ctx.send(embed=embed)

    @lober.command(name="fact")
    async def fact(self, ctx: commands.Context):
        rand = random.choice(ConfigData.lober.data["facts"])
        embed = discord.Embed(
            title="Fact",
            description=rand,
            colour=discord.Colour.dark_gray
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun())
