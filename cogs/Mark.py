from util.DiscordUtil import *
from storage.Database import *
from storage import Cache
import discord
from discord.ext import commands


class Mark(commands.Cog):

    @commands.command("markconfig")
    async def config(self, ctx: commands.Context, *args):
        pass

    @commands.command(name="mark")
    async def mark(self, ctx: commands.Context, *args):
        pass
