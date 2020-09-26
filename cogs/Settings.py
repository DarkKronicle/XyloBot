from util.DiscordUtil import *
import discord
from discord.ext import commands


class Settings(commands.Cog):
    channel_list = {
        "setup": "Where user's get verified",
        "setup-logs": "Where information about verification goes.",
        "qotd": "Where the question of the day is posted!"
    }

    role_list = {
        "verifier": "Verifies users",
        "botmanager": "Can manage the bot"
    }

    @commands.group(name="settings")
    @is_allowed()
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Settings Help",
                description="View commands for configuring Xylo.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="Verification", value="To see verification settings use `>verification`")
            embed.add_field(name="`channel`", value="Configure what channels Xylo uses!")
            embed.add_field(name="`role`", value="Configure what roles Xylo uses!")
            await ctx.send(embed=embed)

    @settings.command(name="channel")
    async def channel(self, ctx: commands.Context, *args):
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
                await ctx.send(f"The `{args[0]}` channel has been set to {channel.mention}")

            else:
                db = Database()
                settings = db.get_settings(str(ctx.guild.id))
                if "channels" not in settings:
                    settings["channels"] = {}
                settings["channels"][args[0]] = ""
                db.set_settings(str(ctx.guild.id), settings)
                await ctx.send(f"The `{args[0]}` channel has been removed!")

        else:
            await ctx.send("Channel name is incorrect! see `>settings channel list`")
            return

    @settings.command(name="role")
    async def role(self, ctx: commands.Context, *args):
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
                await ctx.send(f"The `{args[0]}` role has been set to {role.name}")

            else:
                db = Database()
                settings = db.get_settings(str(ctx.guild.id))
                if "roles" not in settings:
                    settings["roles"] = {}
                settings["roles"][args[0]] = ""
                db.set_settings(str(ctx.guild.id), settings)
                await ctx.send(f"The `{args[0]}` role has been removed!")

        else:
            await ctx.send("Role name is incorrect! see `>settings role list`")
            return


def setup(bot):
    bot.add_cog(Settings())
