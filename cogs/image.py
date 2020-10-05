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
        message.attachments
        pass


def setup(bot):
    bot.add_cog(bot)
