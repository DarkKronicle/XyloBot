"""
A class to allow server moderators to disable/enable commands for specific channels or for the whole server.

This is loosely based off of https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/config.py.
"""
from typing import Optional

import discord
from discord.ext import commands

from storage import db
from util import storage_cache, checks
from util.context import Context
from xylo_bot import XyloBot


class CommandConfig(db.Table, table_name="command_config"):
    # Because there we be lots of repeats within all of the different fields
    id = db.PrimaryKeyColumn()

    # When we call for permissions, we get everything from guild_id.
    guild_id = db.Column(db.Integer(big=True), index=True)
    channel_id = db.Column(db.Integer(big=True), nullable=True)

    # Will the command be an exception to a deny, or be a deny?
    allow = db.Column(db.Boolean())

    # Command name that will be checked.
    name = db.Column(db.String(length=100))


class CommandName(commands.Converter):
    async def convert(self, ctx, argument):
        lowered = argument.lower()

        commands = []
        bot: XyloBot = ctx.bot

        for cmd in bot.walk_commands():
            if cmd.cog_name not in ('Config') and not cmd.hidden:
                commands.append(cmd.qualified_name)

        if lowered not in commands:
            return None

        return lowered


class CommandPermissions:
    class _PermissionData:
        def __init__(self):
            self.allowed = set()
            self.denied = set()

    def __init__(self, guild_id, db_rows):
        self._storage = {}
        self.guild_id = guild_id

        for row in db_rows:
            # For each row we have a channel_id, allow, and name.
            channel_id = row['channel_id']
            name = row['name']
            allow = row['allow']
            if channel_id is None:
                # If no channel then it's a guild thing.
                channel_id = guild_id

            # Put it in...
            if self._storage[channel_id] is None:
                self._storage[channel_id] = self._PermissionData()

            # Add info baby.
            data = self._storage[channel_id]
            if allow:
                data.allowed.add(name)
            else:
                data.denied.add(name)

    # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/config.py#L101
    # MPL-2.0
    def _split(self, obj):
        # "hello there world" -> ["hello", "hello there", "hello there world"]
        from itertools import accumulate
        return list(accumulate(obj.split(), lambda x, y: f'{x} {y}'))

    def _is_command_allowed(self, name, channel_id):
        """
        This function only checks for the boolean. It has no checks for dmchannel, permissions, or anything else.
        """
        allowed = True
        guild_data = self._storage[self.guild_id]
        if channel_id in self._storage:
            channel_data = self._storage[channel_id]
        else:
            channel_data = None

        commands = self._split(name)

        for command in commands:

            if command in guild_data.allowed:
                allowed = True

            if command in guild_data.denied:
                allowed = False

        if channel_data is not None:
            for command in commands:
                if command in channel_data.allowed:
                    allowed = True

                if command in channel_data.denied:
                    allowed = False

        return allowed

    def is_allowed(self, ctx):
        if len(self._storage) == 0:
            return False

        return self._is_command_allowed(ctx.command.qualified_name, ctx.channel.id)


class CommandSettings(commands.Cog):

    # This will be called a lot
    @storage_cache.cache(maxsize=512)
    async def get_command_config(self, guild_id):
        command = "SELECT channel_id, allow, name FROM command_config WHERE guild_id={};"
        command = command.format(str(guild_id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
            rows = con.fetchall()
        return CommandPermissions(guild_id, rows)

    async def disable_command(self, guild_id, name, channel_id=None):
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name={1} AND channel_id"
        delete = delete.format(str(guild_id), str(name))
        if channel_id is None:
            delete = delete + " IS NULL;"
        else:
            delete = delete + f"={str(channel_id)}"

        if channel_id is None:
            insert = "INSERT INTO command_config(guild_id, allow, name) VALUES ({0}, FALSE, $${1}$$);"
            insert = insert.format(str(guild_id), name)
        else:
            insert = "INSERT INTO command_config(guild_id, channel_id, allow, name) VALUES({0}, {1}, FALSE, $${2}$$);"
            insert = insert.format(str(guild_id), str(channel_id), name)

        async with db.MaybeAcquire() as con:
            con.execute(delete + "\n" + insert)

        self.get_command_config.invalidate(guild_id)

    async def enable_command(self, guild_id, name, channel_id=None):
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name={1} AND channel_id"
        delete = delete.format(str(guild_id), str(name))
        if channel_id is None:
            delete = delete + " IS NULL;"
        else:
            delete = delete + f"={str(channel_id)}"

        if channel_id is None:
            insert = "INSERT INTO command_config(guild_id, allow, name) VALUES ({0}, TRUE, $${1}$$);"
            insert = insert.format(str(guild_id), name)
        else:
            insert = "INSERT INTO command_config(guild_id, channel_id, allow, name) VALUES({0}, {1}, TRUE, $${2}$$);"
            insert = insert.format(str(guild_id), str(channel_id), name)

        async with db.MaybeAcquire() as con:
            con.execute(delete + "\n" + insert)

        self.get_command_config.invalidate(guild_id)

    async def reset_channel(self, guild_id, name, channel_id=None):
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name={1} AND channel_id"
        delete = delete.format(str(guild_id), str(name))
        if channel_id is None:
            delete = delete + " IS NULL;"
        else:
            delete = delete + f"={str(channel_id)}"

        async with db.MaybeAcquire() as con:
            con.execute(delete)

        self.get_command_config.invalidate(guild_id)

    async def is_command_enabled(self, ctx):
        if ctx.guild is None:
            return True

        if await ctx.bot.is_owner(ctx.author):
            return True

        if isinstance(ctx.author, discord.Member):
            mod = ctx.author.guild_permissions.manage_guild
            if mod:
                return True

        guild_perms = await self.get_command_config(ctx.guild.id)
        return guild_perms.is_allowed(ctx)

    @commands.group("!commandconfig", aliases=["!ccommand", "!cc"])
    @checks.is_mod()
    async def commandconfig(self, ctx: Context):
        """
        Disables/Enables commands for guild or channel
        """
        pass

    @commandconfig.command(name="enable")
    @checks.is_mod()
    async def enable_command(self, ctx: Context, channel: Optional[discord.TextChannel], *,
                             command: CommandName = None):
        if command is None:
            return await ctx.send("Please put in a proper command!")
        if channel is None:
            channel_id = None
            name = "the server"
        else:
            channel_id = channel.id
            name = channel.mention

        await self.enable_command(ctx.guild.id, command, channel_id)
        await ctx.send(f"Successfully enabled for {name}!")

    @commandconfig.command(name="disable")
    @checks.is_mod()
    async def disable_command(self, ctx: Context, channel: Optional[discord.TextChannel], *,
                             command: CommandName = None):
        if command is None:
            return await ctx.send("Please put in a proper command!")
        if channel is None:
            channel_id = None
            name = "the server"
        else:
            channel_id = channel.id
            name = channel.mention

        await self.disable_command(ctx.guild.id, command, channel_id)
        await ctx.send(f"Successfully disabled for {name}!")

    @commandconfig.command(name="resetcmd")
    @checks.is_mod()
    async def reset_command(self, ctx: Context, channel: Optional[discord.TextChannel], *,
                             command: CommandName = None):
        if command is None:
            return await ctx.send("Please put in a proper command!")
        if channel is None:
            channel_id = None
            name = "the server"
        else:
            channel_id = channel.id
            name = channel.mention

        await self.enable_command(ctx.guild.id, command, channel_id)
        await ctx.send(f"Successfully deleted for {name}!")


def setup(bot):
    bot.add_cog(CommandSettings())
