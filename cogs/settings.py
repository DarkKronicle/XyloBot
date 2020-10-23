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
    @commands.command(name="!prefix", usage="<new_prefix>", aliases=["!p", "!pre"])
    @checks.is_mod()
    @commands.guild_only()
    async def prefix(self, ctx: commands.Context, *args):
        if len(args) == 1:
            await ctx.send_help('settings prefix')
            return

        prefix = ' '.join(args[1:])
        if len(prefix) > 10:
            await ctx.send("Prefix too large!")
            return

        if "$" in prefix:
            prefix = prefix.replace("$", "\\$")

        db = Database()
        db.set_prefix(str(ctx.guild.id), prefix)
        success = discord.Embed(
            title="Xylo prefix changed!",
            description=f"Prefix changed to `{prefix}`!",
            colour=discord.Colour.green()
        )
        cache.clear_prefix_cache(ctx.guild)
        await ctx.send(embed=success)
        return

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
