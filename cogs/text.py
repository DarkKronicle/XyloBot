import discord
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
            if num == 2:
                data_list[i] = c.upper()
                num = -1
            i = i + 1
            num = num + 1

        await ctx.send(''.join(data_list))

    @commands.command(name="clap")
    async def clap(self, ctx: Context, *args):
        """
        Sends a message like: Hi:clap:how:clap:is:clap:...
        """
        if len(args) == 0:
            return await ctx.send("Please put in a proper phrase.")
        data = ' '.join(args)

        data = data.replace(" ", ":clap:")
        await ctx.send(data)

    @commands.command(name="grade")
    async def grade(self, ctx: Context, *args):
        if len(args) == 0:
            await ctx.send("Make sure to put in grades like this: `grade CURRENT|OUTOF|WEIGHT CURRENT...`")
            return
        grades = []
        total = []
        for arg in args:
            content = arg.split("|")
            if len(content) != 3:
                return await ctx.send("Argument should be: `CURRENT|OUTOF|WEIGHT`")

            try:
                current = float(content[0])
                outof = float(content[1])
                weight = float(content[2]) / 100
                percent = float(current/outof)
            except ValueError:
                return await ctx.send(f"Could not parse arguments for integers. Args were: `f{content[0]} f{content[1]} f{content[2]}")

            grade = {
                "current": current,
                "outof": outof,
                "weight": weight,
                "percent": percent
            }
            grades.append(grade)
            total.append(percent * weight)

        totalpercent = 0.0
        for tot in total:
            totalpercent = totalpercent + tot
        embed = discord.Embed(
            title=f"{str(totalpercent)} - {str(totalpercent / 100 * 4)}",
            colour=discord.Colour.gold()
        )
        message = ""
        for grade in grades:
            message = message + f"`\n{str(grade['current'])}/{str(grade['outof'])}` - `{str(grade['percent'] * 100)}%"
        embed.description = message
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TextCog())
