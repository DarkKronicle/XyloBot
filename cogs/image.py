from discord.ext import commands
import discord
from util.context import Context


class Image(commands.Cog):
    @commands.group(name="edit")
    async def edit(self, ctx):
        pass

    @edit.command(name="approval")
    async def approve(self, ctx: Context):
        message: discord.Message = ctx.message
        if len(message.attachments) == 0:
            await ctx.send("Make sure to send in a file!")
            return


def setup(bot):
    bot.add_cog(bot)
