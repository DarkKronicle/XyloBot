from discord.ext import commands
import discord

from storage import db
from util import checks
from util.context import Context


class GuildStorage(db.Table, table_name="guild_config"):
    guild_id = db.Column(db.Integer(big=True), primary_key=True, index=True)
    prefix = db.Column(db.String(length=15), default=">")
    announcements = db.Column(db.Integer(big=True))


class GuildConfig(commands.Cog):
    """
    Configure general settings for Xylo.
    """
    def __init__(self):
        # It's easier for me to see the full file and message of what it will look like then to
        # Have a lot of \n\n with weird formatting.
        self.start_txt = open(r"data/start.txt", "r").read()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        command = "INSERT INTO guild_config(guild_id) VALUES ({});"
        command = command.format(guild.id)
        async with db.MaybeAcquire() as con:
            con.execute(command)

        await self.send_start(guild.owner)

    @commands.command()
    async def start(self, ctx: Context):
        """
        Have Xylo send you the startup text.

        Could be nice if you want to see some features.
        """
        await self.send_start(ctx.author)

    async def send_start(self, user: discord.User):
        if user.dm_channel is None:
            await user.create_dm()
        await user.dm_channel.send(self.start_txt)

    @commands.group(name="!settings", aliases=["!s", "!set"])
    @checks.is_mod()
    @commands.guild_only()
    async def settings(self, ctx: Context):
        """
        Configure general settings of Xylo.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("!settings")

    @settings.command(name="prefix", usage="<new_prefix>")
    @checks.is_mod()
    @commands.guild_only()
    async def prefix(self, ctx: Context, *args):
        """
        Set the prefix for your guild!
        """
        if len(args) == 0:
            await ctx.send_help('Make sure to specify a new prefix!')
            return

        prefix = ' '.join(args[1:])
        if len(prefix) > 10:
            await ctx.send("Prefix too large!")
            return

        if "$" in prefix:
            prefix = prefix.replace("$", "\\$")

        command = "UPDATE guild_config SET prefix=$${1}$$ WHERE guild_id={0};"
        command = command.format(ctx.guild.id, prefix)
        async with db.MaybeAcquire() as con:
            con.execute(command)

        success = discord.Embed(
            title="Xylo prefix changed!",
            description=f"Prefix changed to `{prefix}`!",
            colour=discord.Colour.green()
        )
        ctx.bot.get_guild_prefix.invalidate(ctx.bot, ctx.guild.id)
        await ctx.send(embed=success)
        return

    @settings.command(name="announcements")
    @checks.is_mod()
    @commands.guild_only()
    async def announce_change(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Set what channel gets Xylo updates and announcements.
        """
        if channel is None:
            return await ctx.send("Make sure you specify a proper channel!")

        if channel.guild.id is not ctx.guild.id:
            return await ctx.send("The channel has to be in the same guild!")

        command = "UPDATE guild_config SET announcements={1} WHERE guild_id={0};"
        command = command.format(ctx.guild.id, channel.id)
        async with db.MaybeAcquire() as con:
            con.execute(command)

        await ctx.send(f"Updated the announcement channel to {channel.mention}!")

    @commands.group(name="!database", hidden=True, aliases=["!d", "!db"])
    @commands.is_owner()
    async def db_config(self):
        pass

    @db_config.command(name="bulkguild")
    @commands.is_owner()
    async def bulk_guild(self, ctx: Context):
        insert = "INSERT INTO guild_config(guild_id) VALUES "
        val = "({0})"
        inserts = []
        for guild in ctx.bot.guilds:
            inserts.append(val.format(str(guild.id)))
        insert = insert + ', '.join(inserts) + " ON CONFLICT guild_id DO NOTHING;"
        async with db.MaybeAcquire() as con:
            con.execute(insert)

        await ctx.send("Bing bada boom!")

    @commands.command("!announce", hidden=True)
    @commands.is_owner()
    async def announce(self, ctx: Context, *args):
        if len(args) == 0:
            return await ctx.send("I thought you were better than this ;-;")
        async with ctx.typing():
            await ctx.bot.send_announcement(' '.join(args))
            await ctx.send("There you go! Sent.")


def setup(bot):
    bot.add_cog(GuildConfig())
