from storage import cache
from util.context import Context
from util.discord_util import *
import discord
from discord.ext import commands


class Settings(commands.Cog):
    """
    Settings for how Xylo works.
    """

    channel_list = {
        "setup": "Where user's get verified",
        "setup-logs": "Where information about verification goes.",
        "qotd": "Where the question of the day is posted!",
        "welcome": "Where Xylo welcomes verified users!",
        "logs": "Misc logs",
        "content-creator": "Channel where content creator notifications will be sent.",
        "games": "Where Xylo games will be played in."
    }

    role_list = {
        "verifier": "Verifies users",
        "unverified": "Someone who is not verified",
        "botmanager": "Can manage the bot",
        "content-creator": "Notifications will get sent in feed channel."
    }

    fun_list = {
        "lober": "Random things about lober!"
    }

    message_list = {
        "join-message": "The message that gets sent to a user on join.",
        "verify-message": "The message that gets sent to a user on verification.",
        "reject-message": "The message that gets sent to a user on rejection."
    }

    @commands.group(name="settings")
    @is_allowed()
    async def settings(self, ctx: commands.Context):
        """
        Settings for Xylo.
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Settings Help",
                description="View commands for configuring Xylo.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="Verification", value="To see verification settings use `>verification`")
            embed.add_field(name="`channel`", value="Configure what channels Xylo uses!")
            embed.add_field(name="`role`", value="Configure what roles Xylo uses!")
            embed.add_field(name="`reset`", value="Reset certain fields for Xylo.")
            embed.add_field(name="`fun`", value="Mess around with fun commands!")
            embed.add_field(name="`message`", value="Change messages")
            embed.add_field(name="`util`", value="Configure utilities")
            await ctx.send(embed=embed)

    @settings.command(name="reset", usage="<category>")
    @commands.guild_only()
    async def reset(self, ctx: commands.Context, *args):
        """
        Resets a category of settings for Xylo.
        """
        if len(args) == 0:
            embed = discord.Embed(
                title="Reset Help",
                description="To reset settings for a category, type in `>storage reset <CATEGORY>`",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="fun", value="Reset the Fun commands")
            embed.add_field(name="messages", value="Reset messages")
            embed.add_field(name="util", value="Reset util storage")
            await ctx.send(embed=embed)

        if args[0] == "fun":
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            settings["fun"] = ConfigData.defaultsettings.data["fun"]
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send("Fun commands has been reset!")
            return

        if args[0] == "messages":
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            settings["messages"] = ConfigData.defaultsettings.data["messages"]
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send("Messages have been reset!")
            return

        if args[0] == "util":
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            settings["utility"] = ConfigData.defaultsettings.data["utility"]
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send("Utility has been reset!")
            return

        await ctx.send("Category not found. Check `>settings reset`.")

    @settings.command(name="channel", usage="<list|current|<channel>>")
    @commands.guild_only()
    async def channel(self, ctx: commands.Context, *args):
        """
        Configure what channels Xylo will use.
        """
        if len(args) == 0:
            error = discord.Embed(
                title="Incorrect Usage",
                description="`>settings channel [list/current/<CHANNEL>]`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=error)
            return

        if args[0] == "current":
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            if "channels" not in settings or len(settings["channels"]) == 0:
                await ctx.send("You don't have any channels configured!")
                return

            embed = discord.Embed(
                title="Channels!",
                description="Here are the channels configured:",
                colour=discord.Colour.purple()
            )
            channels_set = settings["channels"]
            for chan in channels_set:
                if channels_set[chan] == "":
                    continue
                try:
                    chan_id = int(channels_set[chan])
                    channel: discord.TextChannel = ctx.guild.get_channel(chan_id)
                    if channel is None:
                        continue
                    embed.add_field(name=chan, value=channel.mention)
                except ValueError:
                    continue

            await ctx.send(embed=embed)
            return

        if args[0] == "list" or len(args) < 2:
            channels = discord.Embed(
                title="Channels List",
                description="See what channels you can edit. Edit one with `>settings channel <CHANNEL> <ID or [none]>`",
                colour=discord.Colour.purple()
            )
            for name in self.channel_list:
                channels.add_field(name=name, value=self.channel_list[name])

            await ctx.send(embed=channels)
            return

        if args[0] in self.channel_list:
            if args[1] != "none":
                try:
                    channel = ctx.guild.get_channel(int(args[1]))
                except ValueError:
                    channel = None
                if channel is None:
                    await ctx.send("Channel ID is incorrect!")
                    return

                db = Database()
                settings = db.get_settings(str(ctx.guild.id))
                if "channels" not in settings:
                    settings["channels"] = {}
                settings["channels"][args[0]] = str(channel.id)
                db.set_settings(str(ctx.guild.id), settings)
                cache.clear_setup_cache(ctx.guild)
                cache.clear_setup_log_cache(ctx.guild)
                cache.clear_game_cache(ctx.guild)
                await ctx.send(f"The `{args[0]}` channel has been set to {channel.mention}")

            else:
                db = Database()
                settings = db.get_settings(str(ctx.guild.id))
                if "channels" not in settings:
                    settings["channels"] = {}
                settings["channels"][args[0]] = ""
                db.set_settings(str(ctx.guild.id), settings)
                cache.clear_setup_cache(ctx.guild)
                cache.clear_setup_log_cache(ctx.guild)
                cache.clear_game_cache(ctx.guild)
                await ctx.send(f"The `{args[0]}` channel has been removed!")

        else:
            await ctx.send("Channel name is incorrect! see `>settings channel list`")
            return

    @settings.command(name="role", usage="<list|current|<role>>")
    @commands.guild_only()
    async def role(self, ctx: commands.Context, *args):
        """
        Configure's what roles Xylo uses.
        """
        if len(args) == 0:
            error = discord.Embed(
                title="Incorrect Usage",
                description="`>settings role [list/current/<role>]`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=error)
            return

        if args[0] == "current":
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            if "roles" not in settings or len(settings["roles"]) == 0:
                await ctx.send("You don't have any roles configured!")
                return

            embed = discord.Embed(
                title="Roles!",
                description="Here are the roles configured:",
                colour=discord.Colour.purple()
            )
            roles_set = settings["roles"]
            for role in roles_set:
                if roles_set[role] == "":
                    continue
                try:
                    chan_id = int(roles_set[role])
                    rl: discord.Role = ctx.guild.get_role(chan_id)
                    if rl is None:
                        continue
                    embed.add_field(name=role, value=rl.name)
                except ValueError:
                    continue

            await ctx.send(embed=embed)
            return

        if args[0] == "list" or len(args) < 2:
            roles = discord.Embed(
                title="Roles List",
                description="See what roles you can edit. Edit one with `>settings role <ROLE> <ID or [none]>`",
                colour=discord.Colour.purple()
            )
            for name in self.role_list:
                roles.add_field(name=name, value=self.role_list[name])

            await ctx.send(embed=roles)
            return

        if args[0] in self.role_list:
            if args[1] != "none":
                try:
                    role = ctx.guild.get_role(int(args[1]))
                except ValueError:
                    role = None
                if role is None:
                    await ctx.send("Role ID is incorrect!")
                    return

                db = Database()
                settings = db.get_settings(str(ctx.guild.id))
                if "roles" not in settings:
                    settings["roles"] = {}
                settings["roles"][args[0]] = str(role.id)
                db.set_settings(str(ctx.guild.id), settings)
                cache.clear_unverified_cache(ctx.guild)
                cache.clear_content_cache(ctx.guild)
                await ctx.send(f"The `{args[0]}` role has been set to {role.name}")

            else:
                db = Database()
                settings = db.get_settings(str(ctx.guild.id))
                if "roles" not in settings:
                    settings["roles"] = {}
                settings["roles"][args[0]] = ""
                db.set_settings(str(ctx.guild.id), settings)
                cache.clear_unverified_cache(ctx.guild)
                cache.clear_content_cache(ctx.guild)
                await ctx.send(f"The `{args[0]}` role has been removed!")

        else:
            await ctx.send("Role name is incorrect! see `>settings role list`")
            return

    @settings.command(name="fun", usage="<list|current|<name>>")
    @commands.guild_only()
    async def fun(self, ctx: commands.Context, *args):
        """
        Toggle and configure fun commands.
        """
        if len(args) == 0:
            embed = discord.Embed(
                title="Fun Help",
                description="`fun <list/current/[NAME]>",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)
            return

        if args[0] == "list":
            embed = discord.Embed(
                title="Current Fun Commands",
                description="Toggle with `fun [NAME]`",
                colour=discord.Colour.purple()
            )
            for name in self.fun_list:
                embed.add_field(name=name, value=self.fun_list[name])
            await ctx.send(embed=embed)
            return

        if args[0] == "current":
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            if "fun" not in settings:
                await ctx.send("No fun commands found! Reset with `>settings reset fun`")
                return
            embed = discord.Embed(
                title="Current Fun Command Settings",
                description="Toggle with `fun [NAME]`",
                colour=discord.Colour.purple()
            )
            for name in settings["fun"]:
                embed.add_field(name=name, value=str(settings["fun"][name]))

            await ctx.send(embed=embed)
            return

        if args[0] in self.fun_list:
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            if "fun" not in settings:
                settings["fun"] = {}
            if args[0] in settings["fun"]:
                enabled = settings["fun"][args[0]]
            else:
                enabled = False

            settings["fun"][args[0]] = not enabled
            db.set_settings(str(ctx.guild.id), settings)
            if not enabled:
                await ctx.send(f"Toggled on {args[0]}")
            else:
                await ctx.send(f"Toggled off {args[0]}!")
            cache.clear_fun_cache(ctx.guild)
            return

        await ctx.send("Module not found. Check `fun list`")

    @settings.group(name="message", usage="<list|current|<name>>", invoke_without_command=True)
    async def message(self, ctx: commands.Context, *args):
        if len(args) == 0:
            embed = discord.Embed(
                title="Message Editing Help",
                description="`message <list/current/[NAME]> [<NEW>]",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)
            return

        if args[0] == "list":
            embed = discord.Embed(
                title="Messages",
                description="`message [NAME] [NEW]`",
                colour=discord.Colour.dark_green()
            )
            for mess in self.message_list:
                embed.add_field(name=mess, value=self.message_list[mess])
            await ctx.send(embed=embed)
            return

        if args[0] == "current":
            embed = discord.Embed(
                title="Current Messages",
                description="What you have set. {server} is server name. {channel} is setup channel (only for join)",
                colour=discord.Colour.green()
            )
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            if "messages" not in settings:
                embed.add_field(name="NONE", value="Reset using `>storage reset`!")
                await ctx.send(embed=embed)
                return

            for mess in settings["messages"]:
                embed.add_field(name=mess, value=settings["messages"][mess])

            await ctx.send(embed=embed)
            return

        if len(args) < 2:
            await ctx.send("You need to put in more information! `messages [NAME] [NEW]")

        if args[0] in self.message_list:
            content = ' '.join(args[1:])
            db = Database()
            settings = db.get_settings(str(ctx.guild.id))
            if 'messages' not in settings:
                settings["messages"] = {}
            settings["messages"][args[0]] = content
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send("Changed message!")
            return

        await ctx.send("Message not found!")

    @settings.group(name="util", invoke_without_command=True)
    async def util(self, ctx: commands.Context):
        """
        Configure utility commands.
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Util Help",
                description="`util <list/current/[NAME]>`",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)
            return

    @util.command(name="list")
    @commands.guild_only()
    async def util_list(self, ctx):
        """
        Lists currently active util commands
        """
        embed = discord.Embed(
            title="Utility commands!",
            description="Edit what commands people have access to.",
            colour=discord.Colour.purple()
        )
        embed.add_field(name="`invite <toggle/CHANNELID>`",
                        value="Allow for Xylo to create tempory invites for quick use.")
        embed.add_field(name="`weather <loc>", value="Configure default weather location.")
        await ctx.send(embed=embed)
        return

    @util.group(name="invite", invoke_without_command=True, usage="<toggle|channel>")
    async def invite(self, ctx):
        """
        Configure the invite command
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('settings invite')

    @invite.command(name="toggle")
    @is_allowed()
    @commands.guild_only()
    async def invite_toggle(self, ctx):
        """
        Toggle the invite command.
        """
        db = Database()
        data = db.get_settings(str(ctx.guild.id))
        if "utility" not in data or "invite" not in data["utility"]:
            await ctx.send("No data found for utility! Use `>settings reset util`")
            return
        if "channel" not in data["utility"]["invite"] or ctx.guild.get_channel(
                data["utility"]["invite"]["channel"]) is None:
            await ctx.send("Can't turn on invite if no channel is set!")
            return

        on = not data["utility"]["invite"]["enabled"]
        data["utility"]["invite"]["enabled"] = on
        db.set_settings(str(ctx.guild.id), data)
        if on:
            await ctx.send("Invite enabled!")
            return
        else:
            await ctx.send("Invite disabled!")
            return

    @invite.command(name="channel")
    @commands.guild_only()
    @is_allowed()
    async def invite_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Set the channel for settings invite.
        """
        if channel is None:
            await ctx.send("You need to specify a proper channel.")
            return

        db = Database()
        data = db.get_settings(str(ctx.guild.id))
        if "utility" not in data:
            data["utility"] = {}
        if "invite" not in data["utility"]:
            data["utility"]["invite"] = {}

        data["utility"]["invite"]["channel"] = channel.id
        db.set_settings(str(ctx.guild.id), data)
        await ctx.send(f"Invite channel set to {channel.mention}!")

    @settings.command(name="prefix", usage="<new_prefix>")
    @is_allowed()
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

    @util.command(name="weather", usage="<loc>")
    @is_allowed()
    @commands.guild_only()
    async def weather(self, ctx: Context, *args):
        """
        Configure weather data for the server.
        """
        if len(args) == 0:
            await ctx.send_help('settings weather')
            return

        if args[0] == "loc":
            if len(args) < 3:
                await ctx.send_help('settings loc <city> <country>')
                return
            if len(args[2]) != 2:
                return await ctx.send("Country must be 2 characters!")

            db = Database()
            data = db.get_settings(str(ctx.guild.id))
            if "utility" not in data:
                data["utility"] = {}
            if "weather" not in data["utility"]:
                data["utility"]["weather"] = {}
            data["utility"]["weather"]["city"] = args[1]
            data["utility"]["weather"]["country"] = args[2]
            db.set_settings(str(ctx.guild.id), data)
            return await ctx.send("Default weather set!")


def setup(bot):
    bot.add_cog(Settings())
