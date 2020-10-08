import os
from datetime import datetime

import discord
from discord.ext import commands

from util.context import Context
from xylo_bot import XyloBot
from pyowm.owm import OWM
from pyowm.weatherapi25 import weather

stats_messages = {}


class Stats(commands.Cog):
    """
    Manages statistic channels that can be customized by staff, as well as stastics for everyday stuff.
    """
    API_key = os.getenv('WEATHER_TOKEN')
    city_name = int(os.getenv('CITY_CODE'))
    owm = OWM(API_key)
    mgr = owm.weather_manager()

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

    @commands.command(name="weather")
    @commands.cooldown(2, 60, commands.BucketType.guild)
    async def weather(self, ctx: Context):
        """
        Gets the current weather
        """
        if ctx.guild.id != 731284440642224139:
            return

        observation = self.mgr.weather_at_id(self.city_name)
        w: weather.Weather = observation.weather

        temp = w.temperature('fahrenheit')
        message = "Temperature:" \
                  f"- Right now: `{temp['temp']}`\n- Low: `{temp['temp_min']}`\n- High: `{temp['temp_min']}`\n- Feels like: `{temp['feels_like']}`\n\n" \
                  f"Current Status: `{w.detailed_status}`" \
                  f"Wind: `{str(w.wind()['speed'])}`" \
                  f"Clouds: `{str(w.clouds)}%`"
        await ctx.send(embed=discord.Embed(
            title="Current Weather",
            description=message,
            colour=discord.Colour.blue()
        ))


def setup(bot):
    bot.add_cog(Stats(bot))
