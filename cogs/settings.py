from storage import cache
from util import checks
from util.context import Context
from util.discord_util import *
import discord
from discord.ext import commands


class Settings(commands.Cog):
    """
    Settings for how Xylo works.
    """

    # TODO Two commands left!


    # @util.command(name="weather", usage="<loc>")
    # @is_allowed()
    # @commands.guild_only()
    # async def weather(self, ctx: Context, *args):
    #     """
    #     Configure weather data for the server.
    #     """
    #     if len(args) == 0:
    #         await ctx.send_help('settings weather')
    #         return
    #
    #     if args[0] == "loc":
    #         if len(args) < 3:
    #             await ctx.send_help('settings loc <city> <country>')
    #             return
    #         if len(args[2]) != 2:
    #             return await ctx.send("Country must be 2 characters!")
    #
    #         db = Database()
    #         data = db.get_settings(str(ctx.guild.id))
    #         if "utility" not in data:
    #             data["utility"] = {}
    #         if "weather" not in data["utility"]:
    #             data["utility"]["weather"] = {}
    #         data["utility"]["weather"]["city"] = args[1]
    #         data["utility"]["weather"]["country"] = args[2]
    #         db.set_settings(str(ctx.guild.id), data)
    #         return await ctx.send("Default weather set!")


def setup(bot):
    bot.add_cog(Settings())
