import random

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
    @commands.cooldown(1, 30, commands.BucketType.user)
    @lober()
    async def lober(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Lober Help",
                description="What lober commands I got.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`>lober fact`", value="View a random lober fact!")
            embed.add_field(name="`>lober image`", value="View a lober image!")
            await ctx.send(embed=embed)

    @lober.command(name="fact")
    async def fact(self, ctx: commands.Context):
        rand = random.choice(ConfigData.lober.data["facts"])
        embed = discord.Embed(
            title="Fact",
            description=rand,
            colour=discord.Colour.dark_gray()
        )
        await ctx.send(embed=embed)

    @lober.command(name="image")
    async def image(self, ctx: commands.Context):
        await ctx.send(content="**LOBER MOMENT**", file=get_file_from_image("https://media.discordapp.net/attachments/757781442674688041/759604260110598144/i64khd2lbns41.png?width=693&height=687", "lober.png"))


def setup(bot):
    bot.add_cog(Fun())