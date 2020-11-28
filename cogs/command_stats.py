import os
from pathlib import Path

from discord.ext import commands

import json

STATS_FILE = "data/stats.json"


class CommandStats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        exists = os.path.exists(STATS_FILE)
        with open(file=STATS_FILE, mode="a+") as f:
            f.seek(0)
            if exists:
                self.data = json.load(f)
            else:
                self.data = {}

    def cog_unload(self):
        with open(file=STATS_FILE, mode='w') as json_file:
            json.dump(self.data, json_file, indent=4, sort_keys=True)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        command = ctx.command.qualified_name
        self.data[command] += 1


def setup(bot):
    bot.add_cog(CommandStats(bot))
