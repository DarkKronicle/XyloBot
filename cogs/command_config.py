"""
A class to allow server moderators to disable/enable commands for specific channels or for the whole server.

This is loosely based off of https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/config.py.
"""
from io import StringIO
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
            if cmd.cog_name != 'CommandSettings' and not cmd.hidden:
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
            if channel_id not in self._storage:
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
            return True

        return self._is_command_allowed(ctx.command.qualified_name, ctx.channel.id)

    def get_data(self, channel_id=None):
        if channel_id is None:
            channel_id = self.guild_id
        if channel_id not in self._storage:
            return None
        return self._storage[channel_id]


class CommandSettings(commands.Cog):
    """
    Disable specific commands per channel or guild.
    """

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
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name=$${1}$$ AND channel_id"
        delete = delete.format(str(guild_id), str(name))
        if channel_id is None:
            delete = delete + " IS NULL;"
        else:
            delete = delete + f"={str(channel_id)};"

        if channel_id is None:
            insert = "INSERT INTO command_config(guild_id, allow, name) VALUES ({0}, FALSE, $${1}$$);"
            insert = insert.format(str(guild_id), name)
        else:
            insert = "INSERT INTO command_config(guild_id, channel_id, allow, name) VALUES({0}, {1}, FALSE, $${2}$$);"
            insert = insert.format(str(guild_id), str(channel_id), name)

        async with db.MaybeAcquire() as con:
            con.execute(delete + "\n" + insert)

        self.get_command_config.invalidate(self, guild_id)

    async def bulk_disable_command(self, guild_id, commands):
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name IN ($${1}$$) AND channel_id IS NULL;"
        delete = delete.format(str(guild_id), '$$, $$'.join(commands))
        insert = "INSERT INTO command_config(guild_id, allow, name) VALUES "
        val = "({0}, FALSE $${1}$$)"
        inserts = []
        for command in commands:
            inserts.append(val.format(str(guild_id), command))
        insert = insert + ', '.join(inserts) + ";"
        async with db.MaybeAcquire() as con:
            con.execute(delete + "\n" + insert)

        self.get_command_config.invalidate(self, guild_id)

    async def enable_command(self, guild_id, name, channel_id=None):
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name=$${1}$$ AND channel_id"
        delete = delete.format(str(guild_id), str(name))
        if channel_id is None:
            delete = delete + " IS NULL;"
        else:
            delete = delete + f"={str(channel_id)};"

        if channel_id is None:
            insert = "INSERT INTO command_config(guild_id, allow, name) VALUES ({0}, TRUE, $${1}$$);"
            insert = insert.format(str(guild_id), name)
        else:
            insert = "INSERT INTO command_config(guild_id, channel_id, allow, name) VALUES({0}, {1}, TRUE, $${2}$$);"
            insert = insert.format(str(guild_id), str(channel_id), name)

        async with db.MaybeAcquire() as con:
            con.execute(delete + "\n" + insert)

        self.get_command_config.invalidate(self, guild_id)

    async def reset_channel(self, guild_id, name, channel_id=None):
        delete = "DELETE FROM command_config WHERE guild_id={0} AND name=$${1}$$ AND channel_id"
        delete = delete.format(str(guild_id), str(name))
        if channel_id is None:
            delete = delete + " IS NULL;"
        else:
            delete = delete + f"={str(channel_id)};"

        async with db.MaybeAcquire() as con:
            con.execute(delete)

        self.get_command_config.invalidate(self, guild_id)

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

    @commands.group("!commandconfig", aliases=["!ccommand", "!cc"], invoke_without_command=True)
    @commands.guild_only()
    @checks.is_mod()
    async def commandconfig(self, ctx: Context):
        """
        Disables/Enables commands for guild or channel
        """
        await ctx.send_help('!commandconfig')

    @commandconfig.command(name="enable")
    @commands.guild_only()
    @checks.is_mod()
    async def config_enable_command(self, ctx: Context, channel: Optional[discord.TextChannel], *,
                                    command: CommandName = None):
        """
        Enables a command. If you don't specify the channel it will do the full server.
        """
        if command is None:
            return await ctx.send("Please put in a proper command!")
        if channel is None:
            channel_id = None
            name = "the server"
        else:
            channel_id = channel.id
            name = channel.mention

        await self.enable_command(ctx.guild.id, command, channel_id=channel_id)
        await ctx.send(f"Successfully enabled for {name}!")

    @commandconfig.command(name="disable")
    @commands.guild_only()
    @checks.is_mod()
    async def config_disable_command(self, ctx: Context, channel: Optional[discord.TextChannel], *,
                                     command: CommandName = None):
        """
        Disables a command. If you don't specify the channel it will do the full server.
        """
        if command is None:
            return await ctx.send("Please put in a proper command!")
        if channel is None:
            channel_id = None
            name = "the server"
        else:
            channel_id = channel.id
            name = channel.mention

        await self.disable_command(ctx.guild.id, command, channel_id=channel_id)
        await ctx.send(f"Successfully disabled for {name}!")

    @commandconfig.command(name="resetcmd")
    @checks.is_mod()
    @commands.guild_only()
    async def config_reset_command(self, ctx: Context, channel: Optional[discord.TextChannel], *,
                                   command: CommandName = None):
        """
        Clears a current setting from the database. If channel is not specified it will do the guild.
        """
        if command is None:
            return await ctx.send("Please put in a proper command!")
        if channel is None:
            channel_id = None
            name = "the server"
        else:
            channel_id = channel.id
            name = channel.mention

        await self.reset_channel(ctx.guild.id, command, channel_id=channel_id)
        await ctx.send(f"Successfully deleted for {name}!")

    @commandconfig.command(name="whitelistcmd", aliases=["white", "whitelist", "wcmd"])
    @checks.is_mod()
    @commands.guild_only()
    async def config_whitelist_command(self, ctx: Context, channel: discord.TextChannel = None, *,
                                       command: CommandName = None):
        """
        Whitelists the command to the specified channel.

        Essentially disables the command on the guild then enables it on this channel. Whitelisting one command multiple
        times will add for all.
        """
        if channel is None or command is None:
            return await ctx.send_help('!commandconfig whitelistcmd')
        await self.disable_command(ctx.guild.id, command, channel_id=channel.id)
        await self.enable_command(ctx.guild.id, command, channel_id=channel.id)

    @commandconfig.command(name="info")
    @checks.is_mod()
    @commands.guild_only()
    async def config_info(self, ctx: Context, channel: Optional[discord.TextChannel]):
        settings = await self.get_command_config(ctx.guild.id)
        if channel is None:
            channel_id = None
        else:
            channel_id = channel.id
        data = settings.get_data(channel_id=channel_id)
        if data is None or (len(data.allowed) == 0 and len(data.denied) == 0):
            return await ctx.send("No command settings for this!")
        message = ""
        if len(data.allowed) != 0:
            message = "Allowed:\n```\n"
            for perms in data.allowed:
                message = message + f"- {perms}\n"
            message = message + "```\n"

        if len(data.denied) != 0:
            message = message + "Denied:\n```\n"
            for perms in data.denied:
                message = message + f"- {perms}\n"

            message = message + "```"
        if len(message) > 2000:
            buffer = StringIO()
            buffer.write(message)
            buffer.seek(0)
            file = discord.File(fp=buffer, filename="file.txt")
            return await ctx.send("There message was too big! Here it is in text.", file=file)
        return await ctx.send(message)

    @commands.group(name="!groupcommandconfig", aliases=["!gcc", "!groupcc", "!mcc"], invoke_without_command=True)
    @checks.is_mod()
    @commands.guild_only()
    async def group_config(self, ctx: Context):
        """
        Shortcuts for disabling different modules of commands.
        """
        await ctx.send_help('!groupcommandconfig')

    @group_config.command(name="verify")
    @checks.is_mod()
    @commands.guild_only()
    async def group_verify(self, ctx: Context):
        """
        Disables all verification settings for guild as well as data settings.
        """
        commands = ["!verify", "auth", "whoami", "whois", "social", "edit", "editother"]
        await self.bulk_disable_command(ctx.guild.id, commands)
        await ctx.send("Successfully disabled commands:\n\n" + ', '.join(commands))

    @group_config.command(name="games")
    @checks.is_mod()
    @commands.guild_only()
    async def group_verify(self, ctx: Context):
        """
        Disables all verification settings for guild as well as data settings.
        """
        commands = ["cah", "quiz", "duel"]
        await self.bulk_disable_command(ctx.guild.id, commands)
        await ctx.send("Successfully disabled commands:\n\n" + ', '.join(commands))

    @group_config.command(name="random")
    @checks.is_mod()
    @commands.guild_only()
    async def group_verify(self, ctx: Context):
        """
        Disables all verification settings for guild as well as data settings.
        """
        commands = ["president", "ship", "product", "idea", "rate"]
        await self.bulk_disable_command(ctx.guild.id, commands)
        await ctx.send("Successfully disabled commands:\n\n" + ', '.join(commands))


def setup(bot):
    bot.add_cog(CommandSettings())
