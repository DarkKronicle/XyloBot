import os
from datetime import datetime

import discord
from discord.ext import commands

from util.context import Context
from xylo_bot import XyloBot
from pyowm.owm import OWM
from pyowm.weatherapi25 import weather
from pyowm.weatherapi25.location import Location
from pyowm.commons.exceptions import NotFoundError

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
    async def weather(self, ctx: Context, *args):
        """
        Gets the current weather.
        """
        if len(args) == 0:
            return await ctx.send('Specify a city. `weather "Tokyo,JP"')

        # observation = self.mgr.weather_at_id(self.city_name)
        try:
            observation = self.mgr.weather_at_place(args[0])
            w: weather.Weather = observation.weather
            location: Location = observation.location
        except NotFoundError:
            return await ctx.send("That cities weather was not found!")
        temp = w.temperature('fahrenheit')
        message = "Temperature:\n" \
                  f"- Right now: `{temp['temp']}`\n- Low: `{temp['temp_min']}F`\n- High: `{temp['temp_max']}F`\n- " \
                  f"Feels like: `{temp['feels_like']}F`\n\n" \
                  f"Current Status: `{w.detailed_status}`\n" \
                  f"Wind: `{str(w.wind(unit='miles_hour')['speed'])}MPH`\n" \
                  f"Clouds: `{str(w.clouds)}%`\n"
        embed = discord.Embed(
            title=f"Current Weather at {location.name}",
            description=message,
            colour=discord.Colour.blue()
        )
        embed.set_thumbnail(url=w.weather_icon_url())
        embed.set_footer(text=f"City: {location.name}. Country: {location.country}. Coord: {location.lon}, {location.lat}")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
