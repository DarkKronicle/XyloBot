from discord.ext import commands

from util.context import Context


class TextCog(commands.Cog, name="text"):

    @commands.command(name="mock", aliases=["mocking", "spongebob"])
    async def mock(self, ctx: Context, *args):
        """
        Makes text like: yoU aRe baD
        """
        if len(args) == 0:
            return await ctx.send("Please put in proper phrase.")
        data = ' '.join(args).lower()

        i = 0
        num = 0
        data_list = list(data)
        length = len(data_list)
        while i < length:
            c = data_list[i]
            if num == 3:
                data_list[i] = c.upper()
                num = -1
            i = i + 1
            num = num + 1

        await ctx.send(''.join(data_list))


def setup(bot):
    bot.add_cog(TextCog())
