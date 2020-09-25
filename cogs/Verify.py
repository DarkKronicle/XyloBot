from util.DiscordUtil import *
import discord
from util.DiscordUtil import *
from discord.ext import commands


def key_or_false(data: dict, key: str):
    if key in data:
        return data[key]
    return False


class Verify(commands.Cog):

    @commands.group(name="verification")
    @is_allowed()
    async def verification(self, context):
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                title="Verification Help",
                description="View commands for verification.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`info`", value="View what verification settings are enabled.")
            embed.add_field(name="`reset`", value="Reset verification information for your server.")
            await context.send(embed=embed)

    @verification.command(name="reset")
    async def reset(self, ctx: commands.Context):
        db = Database()
        if db.guild_exists(str(ctx.guild.id)):
            settings = db.get_settings(str(ctx.guild.id))
            settings["verification"] = ConfigData.defaultsettings["verification"]
        else:
            db.default_settings(str(ctx.guild.id))
        await ctx.send("Reset verification information!")

    @verification.command(name="info")
    async def info(self, ctx: commands.Context):
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if settings is None:
            db.default_settings(str(ctx.guild.id))
            await ctx.send("You didn't have settings. Creating now.")
        if "verification" in settings:
            info = discord.Embed(
                title="Information",
                description="What you have enabled.",
                colour=discord.Colour.purple()
            )
            settings = settings["verification"]
            info.add_field(name="Enabled:", value=str(key_or_false(settings, "enabled")))
            info.add_field(name="First Name:", value=str(key_or_false(settings, "first")))
            info.add_field(name="Last Name:", value=str(key_or_false(settings, "last")))
            info.add_field(name="School:", value=str(key_or_false(settings, "school")))
            info.add_field(name="Extra Information:", value=str(key_or_false(settings, "extra")))
            info.add_field(name="Birthday:", value=str(key_or_false(settings, "birthday")))
            await ctx.send(embed=info)

        else:
            await ctx.send("No verification settings found. Please use `verify reset` to reset verification info.")


def setup(bot):
    bot.add_cog(Verify())
