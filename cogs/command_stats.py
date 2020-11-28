from pathlib import Path

from discord.ext import commands

import json

STATS_FILE = Path("data/stats.json")


class CommandStats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        if STATS_FILE.exists():
            self.data = json.load(STATS_FILE)
        else:
            self.data = {}

    def cog_unload(self):
        json.dump(self.data, STATS_FILE, indent=4, sort_keys=True)

    async def on_command(self, ctx):
        command = ctx.command.qualified_name
        self.data[command] += 1


def setup(bot):
    bot.add_cog(CommandStats(bot))
