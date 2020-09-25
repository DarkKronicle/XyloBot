from util.DiscordUtil import *
import discord
from util.DiscordUtil import *
from discord.ext import commands


def key_or_false(data: dict, key: str):
    if key in data:
        return data[key]
    return False


class Verify(commands.Cog):

    names = {
        "enabled": "enabled",
        "first name": "first",
        "last name": "last",
        "school": "school",
        "extra information": "extra",
        "birthday": "birthday"
    }

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
            embed.add_field(name="`toggle`", value="Toggle a verification setting.")
            embed.add_field(name='`channel`', value="Channels for verification.")
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
            info.add_field(name="Enabled", value=str(key_or_false(settings, "enabled")))
            info.add_field(name="First Name", value=str(key_or_false(settings, "first")))
            info.add_field(name="Last Name", value=str(key_or_false(settings, "last")))
            info.add_field(name="School", value=str(key_or_false(settings, "school")))
            info.add_field(name="Extra Information", value=str(key_or_false(settings, "extra")))
            info.add_field(name="Birthday", value=str(key_or_false(settings, "birthday")))
            await ctx.send(embed=info)

        else:
            await ctx.send("No verification settings found. Please use `verify reset` to reset verification info.")

    @verification.command(name="toggle")
    async def toggle(self, ctx: commands.Context, *args):
        if len(args) == 0:
            error = discord.Embed(
                title="Incorrect Usage",
                description="`>verification toggle <SETTING>`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=error)
            return
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if "verification" in settings:
            full_setting = ' '.join(args[0:]).lower()
            if full_setting in self.names:
                setting = self.names[full_setting]
                if setting == "enabled":
                    if not check_verification_channels(ctx.guild):
                        await ctx.send("You need to setup the channels `setup` and `setup-verify` before you can "
                                       "enable! `>settings channel`")
                        return

                if setting in settings["verification"]:
                    enabled = settings["verification"][setting]
                else:
                    enabled = False
                settings["verification"][setting] = not enabled
                db.set_settings(str(ctx.guild.id), settings)
                if enabled:
                    await ctx.send(f"Toggling off {args[0]}.")
                else:
                    await ctx.send(f"Toggling on {args[0]}.")
            else:
                await ctx.send("No setting found by that name. Look through `>verification info`. `>verification "
                               "toggle <SETTING>")
        else:
            await ctx.send("No verification settings found. Please use `verify reset` to reset verification info.")


def setup(bot):
    bot.add_cog(Verify())
