import math
import os
from datetime import datetime

import discord
from discord.ext import commands
from pyowm.weatherapi25.one_call import OneCall

from util.context import Context
from xylo_bot import XyloBot, Database
from pyowm.owm import OWM
from pyowm.weatherapi25 import weather
from pyowm.weatherapi25.weather_manager import WeatherManager
from pyowm.commons.exceptions import NotFoundError
from pyowm.commons import cityidregistry

stats_messages = {}


class Stats(commands.Cog):
    """
    Manages statistic channels that can be customized by staff, as well as stastics for everyday stuff.
    """
    API_key = os.getenv('WEATHER_TOKEN')
    city_name = int(os.getenv('CITY_CODE'))
    owm = OWM(API_key)
    mgr: WeatherManager = owm.weather_manager()
    reg: cityidregistry.CityIDRegistry = owm.city_id_registry()

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

    @commands.command(name="weather", usage="<city> <country>")
    @commands.cooldown(2, 60, commands.BucketType.guild)
    async def weather(self, ctx: Context, *args):
        """
        Gets the current weather.
        """
        if len(args) == 0 and ctx.guild is not None:
            db = Database()
            data = db.get_settings(str(ctx.guild.id))
            if "utility" in data and "weather" in data["utility"]:
                city = data["utility"]["weather"]["city"]
                country = data["utility"]["weather"]["country"]
            else:
                return await ctx.send("You need to specify a city and a country!")
        else:
            city = args[0]
            if len(args) > 1:
                country = args[1]
            else:
                country = None

        if len(args) == 1:
            locations = self.reg.locations_for(city)
        else:
            locations = self.reg.locations_for(city, country=country.upper())
        if len(locations) == 0:
            return await ctx.send("That cities weather was not found!")
        if len(locations) > 1:
            message = "Multiple cities were found, please type in the number of the one you want.\n"
            i = 0
            for loc in locations:
                i = i + 1
                message = message + f"**{i}**  `{str(loc.id)}` - {loc.name}, {loc.country}: `{loc.lat}` `{loc.lon}`\n"
            answer = await ctx.ask(message)
            if answer is None:
                return await ctx.timeout()
            try:
                val = int(answer)
            except ValueError:
                return await ctx.send("You need to type in a number!")
            i = 0
            location = None
            for loc in locations:
                i = i + 1
                if i == val:
                    location = loc
            if location is None:
                return await ctx.send("Incorrect number!", delete_after=15)
        else:
            location = locations[0]

        weather = await self.get_weather_embed(location)
        await ctx.send(embed=weather)

    async def get_weather_embed(self, loc):
        one_call: OneCall = self.mgr.one_call(lat=loc.lat, lon=loc.lon, units='imperial', exclude="minutely, hourly")

        current: weather.Weather = one_call.current
        temp = math.ceil(current.temp["temp"])
        feel = math.ceil(current.temp["feels_like"])
        today: weather.Weather = one_call.forecast_daily[0]
        temp_low = math.ceil(today.temp["min"])
        temp_high = math.ceil(today.temp["max"])
        message = "Temperature:\n" \
                  f"- Right now: `{str(temp)}F`\n" \
                  f"- High: `{str(temp_high)}F`\n" \
                  f"- Low: `{str(temp_low)}F`\n" \
                  f"- Feels like: `{str(feel)}F`\n" \
                  f"Current Status: `{current.detailed_status}`\n" \
                  f"Clouds: `{str(current.clouds)}%`\n"
        embed = discord.Embed(
            title=f"Current Weather at {loc.name}",
            description=message,
            colour=discord.Colour.blue()
        )
        embed.set_thumbnail(url=current.weather_icon_url())
        embed.set_footer(text=f"City: {loc.name}. Country: {loc.country}. Coord: {loc.lat}, {loc.lon}")
        return embed


def setup(bot):
    bot.add_cog(Stats(bot))
