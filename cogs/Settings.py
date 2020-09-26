from util.DiscordUtil import *
import discord
from discord.ext import commands


class Settings(commands.Cog):
    channel_list = {
        "setup": "Where user's get verified",
        "setup-logs": "Where information about verification goes.",
        "qotd": "Where the question of the day is posted!"
    }

    @commands.group(name="settings")
    @is_allowed()
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Settings Help",
                description="View commands for verification.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="Verification", value="To see verification settings use `>verification`")
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
                description="See what channels you can edit. Edit one with `>settings channel <CHANNEL> <ID or [none]`",
                colour=discord.Colour.purple()
            )
            for name in self.channel_list:
                channels.add_field(name=name, value=self.channel_list[name])

            await ctx.send(embed=channels)
            return

        if args[0] in self.channel_list:
            if args[1] is not "none":
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


def setup(bot):
    bot.add_cog(Settings())
