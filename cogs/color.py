import discord
from discord.ext import commands

from util.context import Context


class Color4:

    def __init__(self, red, green, blue, alpha):
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    @classmethod
    def from_int(cls, rgb):
        alpha = rgb >> 24 & 0xFF
        red = rgb >> 16 & 0xFF
        green = rgb >> 8 & 0xFF
        blue = rgb & 0xFF
        return Color4(red, green, blue, alpha)

    def to_int(self):
        rgb = self.alpha
        rgb = (rgb << 8) + self.red
        rgb = (rgb << 8) + self.green
        rgb = (rgb << 8) + self.blue
        return rgb


class Color(commands.Cog):

    @commands.command(name="colorint")
    async def col(self, ctx: Context, rgb: int):
        color = Color4.from_int(rgb)

        embed = discord.Embed(color=color.to_int(), description=f"Color: {color.to_int()}\n\nR: {color.red}\n\nG: {color.green}\n\nB: {color.blue}\n\nA: {color.alpha}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Color())
