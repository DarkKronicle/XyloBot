from datetime import datetime

import discord
from discord.ext import commands
from xylo_bot import XyloBot

stats_messages = {}


class Stats(commands.Cog):
    """
    Manages statistic channels that can be customized by staff.
    """

    def __init__(self, bot):
        self.bot: XyloBot = bot
        bot.add_loop("stat", self.update_stats)

    async def update_stats(self, time: datetime):
        pass


def setup(bot):
    bot.add_cog(Stats(bot))
