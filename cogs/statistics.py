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

    async def get_stat_channel(self, guild_id):
        if guild_id == 731284440642224139:
            return self.bot.get_channel(763563768004476949)
        return None

    async def update_stats(self, time: datetime):
        channel = self.get_stat_channel(731284440642224139)
        if channel is None:
            return


def setup(bot):
    bot.add_cog(Stats(bot))
