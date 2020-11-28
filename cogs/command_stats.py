import os

import discord
from discord.ext import commands
from collections import Counter

import json

from util.context import Context

STATS_FILE = "data/stats.json"


class CommandStats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        exists = os.path.exists(STATS_FILE)
        with open(file=STATS_FILE, mode="a+") as f:
            f.seek(0)
            if exists:
                self.data = Counter(json.load(f))
            else:
                self.data = Counter()

    def cog_unload(self):
        with open(file=STATS_FILE, mode='w') as json_file:
            json.dump(dict(self.data), json_file, indent=4, sort_keys=True)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        command = ctx.command.qualified_name
        self.data[command] += 1

    @commands.group(name="stats", invoke_without_command=True)
    async def stats(self, ctx: Context, *, command_name="help"):
        """View command stats!"""
        num = self.data.get(command_name, 0)
        if num == 0:
            embed = discord.Embed(description=f"Hmm, looks like I don't have `{command_name}` recorded.")
        else:
            embed = discord.Embed(
                description=f"I have processed a `{command_name}` a total of `{num}` times!",
                colour=discord.Colour.magenta()
            )
        embed.set_footer(text="*Since November 27, 2020")
        await ctx.send(embed=embed)

    @stats.command(name="all")
    async def all_stats(self, ctx: Context):
        """View a sum of all commands!"""
        embed = discord.Embed(
            description=f"I have processed a total of `{sum(self.data.values())}` commands!",
            colour=discord.Colour.magenta()
        )
        embed.set_footer(text="*Since November 27, 2020")
        await ctx.send(embed=embed)

    @stats.command(name="top")
    async def top(self, ctx: Context):
        """View the top most used commands!"""
        common = self.data.most_common(10)
        embed = discord.Embed(
            title="Command Stats",
            description='\n'.join(f'`{k}`: {c}' for k, c in common),
            colour=discord.Colour.gold()
        )
        embed.set_footer(text="*Since November 27, 2020")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CommandStats(bot))
