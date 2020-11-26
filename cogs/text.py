import discord
from discord.ext import commands

from util.context import Context


class TextCog(commands.Cog, name="text"):
    """
    Manipulate text using the power of commands!
    """

    @commands.command(name="mock", aliases=["mocking", "spongebob"])
    async def mock(self, ctx: Context, *, to_mock: commands.clean_content = None):
        """
        Makes text like: yoU aRe baD
        """
        if to_mock is None:
            return await ctx.send("Please put in proper phrase.")

        i = 0
        num = 0
        data_list = list(to_mock)
        length = len(data_list)
        while i < length:
            c = data_list[i]
            if num == 2:
                data_list[i] = c.upper()
                num = -1
            i = i + 1
            num = num + 1

        await ctx.send(''.join(data_list))

    @commands.command(name="clap")
    async def clap(self, ctx: Context, *, to_clap: commands.clean_content = None):
        """
        Sends a message like: Hi:clap:how:clap:is:clap:...
        """
        if to_clap is None:
            return await ctx.send("Please put in proper phrase.")

        data = to_clap.replace(" ", ":clap:")
        await ctx.send(data)


def setup(bot):
    bot.add_cog(TextCog())
