import asyncio
import random

from storage.db import MaybeAcquire
from util import storage_cache, checks
from util.context import Context
from util.discord_util import *
from discord.ext import commands
from storage import db
from xylo_bot import XyloBot


def id_in(id_int, check):
    for user in check:
        if user[0] == id_int:
            return True
    return False


def key_or_false(data: dict, key: str):
    if key in data:
        return data[key]
    return False


def get_true(sets):
    if sets is None:
        return None
    for f in list(sets):
        if not sets[f]:
            sets.pop(f)
    return sets


def get_key(val, settings):
    for key, value in settings.items():
        if val == value:
            return key

    return "key doesn't exist"


def is_verifier_user():
    async def predicate(ctx):
        bot: XyloBot = ctx.bot
        cog = bot.get_cog('Verify')
        settings = await cog.get_verify_config(ctx.guild.id)
        if ctx.channel.id != settings.setup_log_id:
            return False
        return await checks.check_permissions(ctx, {"send_messages": True})

    return commands.check(predicate)


class VerifySettings(db.Table, table_name="verify_settings"):
    guild_id = db.Column(db.Integer(big=True), index=True)

    setup_channel = db.Column(db.Integer(big=True))
    setup_log = db.Column(db.Integer(big=True))
    welcome_channel = db.Column(db.Integer(big=True))

    unverified_role = db.Column(db.Integer(big=True))
    roles = db.Column(db.JSON())

    fields = db.Column(db.JSON())
    active = db.Column(db.Boolean(), default=True)

    messages = db.Column(db.JSON())


class VerifyQueue(db.Table, table_name="verify_queue"):
    guild_id = db.Column(db.Integer(big=True), primary_key=True)
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    data = db.Column(db.JSON())

    @classmethod
    def create_table(cls, *, overwrite=False):
        statement = super().create_table(overwrite=overwrite)
        # create the unique index for guild_id and user_id for SPPEEEEEEDDD
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS verify_queue_uniq_idx ON verify_queue (guild_id, user_id);"
        return statement + '\n' + sql


class VerifyConfig:
    """
    Stores data on how verification is setup for a guild.
    """
    __slots__ = (
        "bot", "guild_id", "setup_channel_id", "setup_log_id", "unverified_role_id", "roles_data", "fields", "active",
        "config", "reject_message", "accept_message", "welcome_channel_id"
    )

    def __init__(self, *, guild_id, bot, data=None):
        self.guild_id = guild_id
        self.bot: XyloBot = bot

        if data is not None:
            self.config = True
            self.active = data['active']
            self.setup_channel_id = data['setup_channel']
            self.setup_log_id = data['setup_log']
            self.welcome_channel_id = data['welcome_channel']
            self.fields = data['fields']
            self.unverified_role_id = data['unverified_role']
            self.roles_data = data['roles']['roles']
            self.reject_message = data['messages']['reject']
            self.accept_message = data['messages']['accept']
        else:
            self.config = False
            self.active = False
            self.setup_channel_id = None
            self.setup_log_id = None
            self.welcome_channel_id = None
            self.fields = None
            self.unverified_role_id = None
            self.roles_data = None
            self.reject_message = None
            self.accept_message = None

    @property
    def welcome_channel(self):
        guild = self.bot.get_guild(self.guild_id)
        return guild.get_channel(self.welcome_channel_id)

    @property
    def setup_channel(self):
        guild = self.bot.get_guild(self.guild_id)
        return guild.get_channel(self.setup_channel_id)

    @property
    def log_channel(self):
        guild = self.bot.get_guild(self.guild_id)
        return guild.get_channel(self.setup_log_id)

    @property
    def unverified_role(self):
        guild = self.bot.get_guild(self.guild_id)
        return guild.get_role(self.unverified_role_id)

    @property
    def roles(self):
        roles = []
        guild = self.bot.get_guild(self.guild_id)
        for role in self.roles_data:
            roles.append(guild.get_role(role))
        return roles


class Verify(commands.Cog):
    """
    Verify new members.
    """

    """
    Start of configuration section for verification.
    """

    # TODO get this working with correct capitals.
    names = {
        "first name": "first",
        "last name": "last",
        "school": "school",
        "extra information": "extra",
        "birthday": "birthday"
    }

    prompts = {
        "first": "What's your first name?",
        "last": "What's your last name?",
        "school": "What school do you go to?",
        "birthday": "What's your birthday? (YYYY-MM-DD)",
        "extra": "What should I know about you?"
    }

    @commands.group(name="!verify", aliases=["!verification", "!v"], invoke_without_command=True)
    @commands.guild_only()
    async def mod_verify(self, ctx: Context):
        """
        Verification settings for your server.
        """
        await ctx.send_help('!verify')

    @mod_verify.command(name="setup")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_setup(self, ctx: Context):
        """
        Uses a setup wizard to get your verification system up and running!
        """
        # Kind of a mess right here... but it works.
        settings = await self.get_verify_config(ctx.guild.id)
        # Don't want to override old preferences, they can still edit using other commands.
        if not settings.config:
            return await ctx.send(
                "This server has already been setup! Have an admin use `!verify clearsettings` if you want to "
                "re-setup the settings.")

        ask_channel = await ctx.raw_ask("What channel should users put in their information? (Use a `#channel` "
                                        "mention.)")
        if ask_channel is None:
            return await ctx.timeout()
        # Use built in discord.py feature to get channel mentions from a message.
        channels = ask_channel.channel_mentions
        if channels is None or len(channels) != 1:
            return await ctx.send("Make sure to put in just one correct channel!")
        channel = channels[0]

        ask_log = await ctx.raw_ask(
            "What channel should I send verification updates to? (User join, user queue, accept users) To "
            "accept/reject a person you have to have permissions to send messages in this channel.")
        if ask_log is None:
            return await ctx.timeout()
        channels = ask_log.channel_mentions
        if channels is None or len(channels) != 1:
            return await ctx.send("Make sure to put in just one correct channel!")
        log = channels[0]

        ask_welcome = await ctx.raw_ask(
            "What channel should I send welcome messages for when a user is verified?")
        if ask_welcome is None:
            return await ctx.timeout()
        channels = ask_welcome.channel_mentions
        if channels is None or len(channels) != 1:
            return await ctx.send("Make sure to put in just one correct channel!")
        welcome = channels[0]

        ask_unverified = await ctx.ask(
            "What's the ID of the role I should give to unverified users? (Enable developer mode and copy ID)",
            timeout=120)
        if ask_unverified is None:
            return await ctx.timeout()
        try:
            role_int = int(ask_unverified)
        except ValueError:
            return await ctx.send("Make sure to put in just the integer.")
        unverified = ctx.guild.get_role(role_int)
        if unverified is None:
            return await ctx.send("Could not find the role.")

        ask_roles = await ctx.ask("What roles should I give to the user when they join? (Separate by spaces and use "
                                  "role ID's. Use `none` if you don't want any)", timeout=180)
        if ask_roles is None:
            return await ctx.timeout()

        roles = []
        if ask_roles != False:
            for role in ask_roles.split(' '):
                try:
                    role_int = int(role)
                except ValueError:
                    return await ctx.send(f"Please put in just an int for the role: {role}")
                role = ctx.guild.get_role(role_int)
                if role is None:
                    return await ctx.send(f"Could not find the role {role}")
                roles.append(role_int)

        # Lists fields with a number by each for easy adding.
        message = "What fields should I ask for? Separate answers by using a space and using the numbers. (If you " \
                  "don't want any fields just use `none`) Allowed fields are:\n "
        field_list = list(self.names)
        i = 0
        for field in field_list:
            i = i + 1
            message = message + f"`{i}: {field}` "

        ask_fields = await ctx.ask(message, timeout=180, allow_none=True)

        if ask_fields is None:
            return await ctx.timeout()

        fields = {}

        # Have to check all of them to make sure it works.
        if not ask_fields == False:
            fs = ask_fields.split(' ')
            filist = []
            for f in fs:
                try:
                    fi = int(f)
                except ValueError:
                    return await ctx.send(f"Make sure you specify an int. Error happened with: `{f}`")
                if fi > i or i < 1:
                    return await ctx.send("Number not in range of possible fields!")
                filist.append(fi)

            i = 0
            for field in field_list:
                i = i + 1
                if i in filist:
                    fields[self.names[field]] = True
                else:
                    fields[self.names[field]] = False
        else:
            for field in field_list:
                fields[self.names[field]] = False

        # Easy use for psql json
        roles_dict = {"roles": roles}
        messages = {
            "accept": f"You have been accepted into {ctx.guild.name}!",
            "reject": f"You have been rejected from {ctx.guild.name}. Try again or contact a staff member if you "
                      f"believe this is a mistake. "
        }

        command = "INSERT INTO verify_settings(guild_id, setup_channel, setup_log, welcome_channel, unverified_role, " \
                  "roles, fields, " \
                  "active, messages) VALUES({0}, {1}, {2}, {3}, $${4}$$, $${5}$$, {6}, $${7}$$); "
        command = command.format(str(ctx.guild.id), str(channel.id), str(log.id), str(welcome.id), str(unverified.id),
                                 json.dumps(roles_dict), json.dumps(fields), "TRUE", json.dumps(messages))
        async with db.MaybeAcquire() as con:
            con.execute(command)

        await ctx.send("You're all setup!")
        await self.mod_verify_current(ctx)

    @mod_verify.command(name="roles")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_roles(self, ctx: Context):
        """
        Sets up the roles Xylo uses for unverified and what to give verified.
        """
        settings = await self.get_verify_config(ctx.guild.id)
        if not settings.config:
            return await ctx.send(embed=discord.Embed(
                title="No Verification Setup",
                description="To edit specific fields you need to go through `!verify setup`.",
                colour=discord.Colour.red()
            ))

        ask_unverified = await ctx.ask(
            "What's the ID of the role I should give to unverified users? (Enable developer mode and copy ID)",
            timeout=120)
        if ask_unverified is None:
            return await ctx.timeout()
        try:
            role_int = int(ask_unverified)
        except ValueError:
            return await ctx.send("Make sure to put in just the integer.")
        unverified = ctx.guild.get_role(role_int)
        if unverified is None:
            return await ctx.send("Could not find the role.")

        ask_roles = await ctx.ask("What roles should I give to the user when they join? (Separate by spaces and use "
                                  "role ID's. Use `none` if you don't want any)", timeout=180)
        if ask_roles is None:
            return await ctx.timeout()

        roles = []
        if ask_roles != False:
            for role in ask_roles.split(' '):
                try:
                    role_int = int(role)
                except ValueError:
                    return await ctx.send(f"Please put in just an int for the role: {role}")
                role = ctx.guild.get_role(role_int)
                if role is None:
                    return await ctx.send(f"Could not find the role {role}")
                roles.append(role_int)

        roles_dict = {"roles": roles}

        command = "UPDATE verify_settings SET unverified_role = {0}, roles = $${1}$$ WHERE guild_id = {2};"
        command = command.format(str(unverified.id), json.dumps(roles_dict), str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(self, ctx.guild.id)
        await self.mod_verify_current(ctx)

    @mod_verify.command(name="channels")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_channels(self, ctx: Context):
        """
        Changes the setup channel and the setup-log channel.

        Setup channel: Where unverified users will see and send messages in to verify.
        Setup log: Where updates about verification gets sent. User joins, user goes through process, verified, rejected
        """
        settings = await self.get_verify_config(ctx.guild.id)
        if not settings.config:
            return await ctx.send(embed=discord.Embed(
                title="No Verification Setup",
                description="To edit specific fields you need to go through `!verify setup`.",
                colour=discord.Colour.red()
            ))

        ask_channel = await ctx.raw_ask("What channel should users put in their information? (Use a `#channel` "
                                        "mention.)")
        if ask_channel is None:
            return await ctx.timeout()
        # Use built in discord.py feature to get channel mentions from a message.
        channels = ask_channel.channel_mentions
        if channels is None or len(channels) != 1:
            return await ctx.send("Make sure to put in just one correct channel!")
        channel = channels[0]

        ask_log = await ctx.raw_ask(
            "What channel should I send verification updates to? (User join, user queue, accept users) To "
            "accept/reject a person you have to have permissions to send messages in this channel.")
        if ask_log is None:
            return await ctx.timeout()
        channels = ask_log.channel_mentions
        if channels is None or len(channels) != 1:
            return await ctx.send("Make sure to put in just one correct channel!")
        log = channels[0]

        ask_welcome = await ctx.raw_ask(
            "What channel should I send welcome messages for when a user is verified?")
        if ask_welcome is None:
            return await ctx.timeout()
        channels = ask_welcome.channel_mentions
        if channels is None or len(channels) != 1:
            return await ctx.send("Make sure to put in just one correct channel!")
        welcome = channels[0]

        command = "UPDATE verify_settings SET setup_channel = {0}, setup_log = {1}, welcome_channel = {2} WHERE guild_id = {3};"
        command = command.format(str(channel.id), str(log.id), str(welcome.id), str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(self, ctx.guild.id)
        await self.mod_verify_current(ctx)

    @mod_verify.command(name="fields")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_fields(self, ctx: Context):
        """
        Configures what fields you want Xylo to ask for.

        Basically is just the step for the setup.
        """
        settings = await self.get_verify_config(ctx.guild.id)
        if not settings.config:
            return await ctx.send(embed=discord.Embed(
                title="No Verification Setup",
                description="To edit specific fields you need to go through `!verify setup`.",
                colour=discord.Colour.red()
            ))

        message = "What fields should I ask for? Separate answers by using a space and using the numbers. (If you " \
                  "don't want any fields just use `none`) Allowed fields are:\n "
        field_list = list(self.names)
        i = 0
        for field in field_list:
            i = i + 1
            message = message + f"`{i}: {field}` "

        ask_fields = await ctx.ask(message, timeout=180, allow_none=True)

        if ask_fields is None:
            return await ctx.timeout()

        fields = {}

        # Have to check all of them to make sure it works.
        if not ask_fields == False:
            fs = ask_fields.split(' ')
            filist = []
            for f in fs:
                try:
                    fi = int(f)
                except ValueError:
                    return await ctx.send(f"Make sure you specify an int. Error happened with: `{f}`")
                if fi > i or i < 1:
                    return await ctx.send("Number not in range of possible fields!")
                filist.append(fi)

            i = 0
            for field in field_list:
                i = i + 1
                if i in filist:
                    fields[self.names[field]] = True
                else:
                    fields[self.names[field]] = False
        else:
            for field in field_list:
                fields[self.names[field]] = False

        command = "UPDATE verify_settings SET fields=$${0}$$ WHERE guild_id={1};"
        command = command.format(json.dumps(fields), str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(self, ctx.guild.id)
        await self.mod_verify_current(ctx)

    @mod_verify.command(name="clearsettings")
    @checks.is_admin()
    @commands.guild_only()
    async def mod_verify_clearsettings(self, ctx: Context):
        """
        Clears settings that are being used for verification.
        """
        answer = await ctx.prompt("Are you sure you want to clear the settings? This will not remove user data or any "
                                  "users in queue. It will disable verification and you will need to go through the "
                                  "`!verify setup` again.")
        if answer is None:
            return await ctx.timeout()
        if not answer:
            return await ctx.send("Cancelling settings clear.")

        command = "DELETE FROM verify_settings WHERE guild_id={};"
        command = command.format(str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(self, ctx.guild.id)
        await ctx.send("Settings have been reset for your guild!")

    @mod_verify.command(name="resetall")
    @checks.is_admin()
    @commands.guild_only()
    async def mod_verify_reset(self, ctx: Context):
        """
        Resets ALL verification system inside of the database. This CANNOT be undone.
        """
        answer = await ctx.prompt(
            "Are you sure you want to reset all verification info? This will **remove all current "
            "verified users** in the system, **remove settings**, and **cannot be undone**. Are you "
            "sure? Respond with yes/no.")
        if answer is None:
            return await ctx.timeout()
        if not answer:
            return await ctx.send("Cancelling reset.")

        delete_settings = "DELETE FROM verify_settings WHERE guild_id={};"
        delete_users = "DELETE FROM user_data WHERE guild_id=$${}$$;"
        delete_queue = "DELETE FROM verify_queue WHERE guild_id={};"
        delete_settings = delete_settings.format(str(ctx.guild.id))
        delete_users = delete_users.format(str(ctx.guild.id))
        delete_queue = delete_queue.format(str(ctx.guild.id))
        command = delete_settings + "\n" + delete_queue + "\n" + delete_users
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(self, ctx.guild.id)
        await ctx.send("All data has been deleted from this server.")

    @mod_verify.command(name="enable")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_enable(self, ctx: Context):
        """
        Enable verification on the server.
        """
        settings = await self.get_verify_config(ctx.guild.id)
        if not settings.config:
            return await ctx.send(embed=discord.Embed(
                title="No Verification Setup",
                description="To enable/disable you need to go through `!verify setup`.",
                colour=discord.Colour.red()
            ))

        if settings.active:
            return await ctx.send("Verification was already enabled.")
        command = "UPDATE verify_settings SET active=TRUE WHERE guild_id={};"
        command = command.format(str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send("Verification has been enabled!")

    @mod_verify.command(name="disable")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_disable(self, ctx: Context):
        """
        Disable verification on the server.
        """
        settings = await self.get_verify_config(ctx.guild.id)
        if not settings.config:
            return await ctx.send(embed=discord.Embed(
                title="No Verification Setup",
                description="To enable/disable you need to go through `!verify setup`.",
                colour=discord.Colour.red()
            ))

        if settings.active:
            return await ctx.send("Verification was already enabled.")
        command = "UPDATE verify_settings SET active=FALSE WHERE guild_id={};"
        command = command.format(str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send("Verification has been disabled!")

    @mod_verify.command(name="messages")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_message(self, ctx: Context):
        """
        Configure the messages that are sent with verification.
        """
        reject = await ctx.ask("What message should I send when a user is rejected?")
        if reject is None:
            return await ctx.timeout()
        if len(reject) > 1000:
            return await ctx.send("Message was too big!")

        accept = await ctx.ask("What message should I send when a user is accepted?")
        if accept is None:
            return await ctx.timeout()
        if len(accept) > 1000:
            return await ctx.send("Message was too big!")

        data = {"accept": accept, "reject": reject}
        command = "UPDATE verify_settings SET messages=$${0}$$ WHERE guild_id={1};"
        command = command.format(json.dumps(data), str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send("Messages updated!")

    @mod_verify.command(name="current")
    @checks.is_mod()
    @commands.guild_only()
    async def mod_verify_current(self, ctx: Context):
        settings: VerifyConfig = await self.get_verify_config(ctx.guild.id)

        if settings.setup_channel_id is None:
            embed = discord.Embed(
                title="No Verification Setup",
                description="This server currently has no verification setup. To set it up use `!verify setup`.",
                colour=discord.Colour.red()
            )
            return await ctx.send(embed=embed)

        setup_channel = settings.setup_channel
        setup_log = settings.log_channel
        unverified_role = settings.unverified_role
        roles = settings.roles
        fields = settings.fields
        active = settings.active
        accept = settings.accept_message
        reject = settings.reject_message
        welcome = settings.welcome_channel
        if active:
            active_str = "Enabled"
        else:
            active_str = "Disabled"
        message = "Current Verification settings. Edit with `>help !verify` commands.\n\nCurrent fields enabled:\n```"

        def format_true(to_format):
            if to_format:
                return "Enabled"
            else:
                return "Disabled"

        for field in fields:
            name = get_key(field, self.names)
            message = message + f"{name} - {format_true(fields[field])}\n"
        message = message + f"\n```\nSetup Channel - {setup_channel.mention}\nSetup Log Channel - {setup_log.mention}" \
                            f"\nWelcome Channel - {welcome.mention}\n" \
                            f"Unverified Role - `{unverified_role.name}`\n" \
                            f"\nOn accept:`{accept}`\nOn reject:`{reject}`\n\nRoles on verification:"
        for role in roles:
            message = message + f"`{role.name}` "

        embed = discord.Embed(
            title=f"Verification {active_str}",
            description=message,
            colour=discord.Colour.green()
        )
        await ctx.send(embed=embed)

    @storage_cache.cache()
    async def get_verify_config(self, guild_id, *, connection=None):
        command = "SELECT setup_channel, setup_log, welcome_channel, unverified_role, roles, fields, active, messages FROM " \
                  "verify_settings WHERE guild_id={};"
        command = command.format(str(guild_id))
        async with MaybeAcquire(connection=connection) as con:
            con.execute(command)
            data = con.fetchone()
        return VerifyConfig(guild_id=guild_id, bot=self.bot, data=data)

    """
    Verification settings done.
    """

    verifying = {}

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def verify_queue(self, member: discord.Member, guild: discord.Guild):
        settings = await self.get_verify_config(guild.id)
        command = "INSERT INTO verify_queue(guild_id, user_id, data) " \
                  "VALUES($${0}$$, $${1}$$, $${2}$$) ON CONFLICT (guild_id, user_id) DO UPDATE SET data = " \
                  "EXCLUDED.data; "
        command = command.format(str(guild.id), str(member.id),
                                 json.dumps(self.verifying[guild.id][member.id]['fields']))
        async with db.MaybeAcquire() as con:
            con.execute(command)

        channel = settings.log_channel
        message = f":bell: `{member.display_name}` just went through the verification process!"
        for field in self.verifying[guild.id][member.id]['fields']:
            message = message + f"\n-    {get_key(field, self.names)}: `{self.verifying[guild.id][member.id]['fields'][field]}`"
        await channel.send(message)

    async def is_done(self, member, guild):
        # If they are already in the system for verification no need to check the database.
        if guild.id in self.verifying and member.id in self.verifying[guild.id]:
            return self.verifying[guild.id][member.id]["done"]
        else:
            return await self._done_cache(guild.id, member.id)

    @storage_cache.cache()
    async def _done_cache(self, guild_id, user_id):
        command = "SELECT user_id FROM verify_queue WHERE guild_id={0} AND user_id={0};"
        command = command.format(str(guild_id), str(user_id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
            user = con.fetchone()
        if user is None:
            return False
        else:
            return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Can't verify bots...
        if message.author.bot:
            return

        # Why would we want to verify a dm?
        if message.guild is None:
            return

        settings = await self.get_verify_config(message.guild.id)

        # Check to see if it's active.
        if not settings.config or not settings.active:
            return

        role = settings.unverified_role
        if role not in message.author.roles:
            return

        channel: discord.TextChannel = settings.setup_channel
        if channel is None or message.channel is not channel:
            return

        # Time to start verifying!
        if message.guild.id not in self.verifying:
            self.verifying[message.guild.id] = {}

        fields = get_true(settings.fields)

        # From here on out logic is a bit of a mess... but it works.
        if await self.is_done(message.author, message.guild):
            await message.delete()
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await channel.send(embed=done, delete_after=15)
            return

        # Current data we have on them.
        if message.author.id in self.verifying[message.guild.id]:
            current = self.verifying[message.guild.id][message.author.id]
        else:
            self.verifying[message.guild.id][message.author.id] = {
                "step": False,
                "done": False,
                "fields": {}
            }
            current = self.verifying[message.guild.id][message.author.id]

        # Are they doing something with verification already.
        if current["step"]:
            return

        await message.delete()


        # If there are no fields enabled we just let staff know that they actually do exist.
        if len(fields) == 0:
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await channel.send(embed=done, delete_after=15)
            await self.verify_queue(message.author, message.guild)
            return

        self.verifying[message.guild.id][message.author.id]["step"] = True
        # TODO I really need to convert this to Context.ask(). Could probably shave off a lot of code.
        for value in fields:
            # Ask them for each field what they are.
            prompt = await channel.send(self.prompts[value])
            try:
                answer = await self.bot.wait_for(
                    "message",
                    timeout=60,
                    check=lambda msg: msg.author == message.author and msg.channel == message.channel
                )
                await prompt.delete()
                await answer.delete()
                if answer:
                    self.verifying[message.guild.id][message.author.id]["fields"][value] = answer.content
            except asyncio.TimeoutError:
                self.verifying[message.guild.id].pop(message.author.id)
                await prompt.delete()
                await channel.send("This has been closed due to a timeout", delete_after=15)
                return

        if self.verifying[message.guild.id][message.author.id] is not None:
            # Format a response of all of their settings.
            response = discord.Embed(
                title="Is this info correct?",
                description="Respond `yes` or `no`",
                colour=discord.Colour.purple()
            )
            for field in self.verifying[message.guild.id][message.author.id]["fields"]:
                response.add_field(name=get_key(field, self.names),
                                   value=self.verifying[message.guild.id][message.author.id]['fields'][field])
            prompt = await channel.send(embed=response)
            try:
                answer = await self.bot.wait_for(
                    "message",
                    timeout=60,
                    check=lambda msg: msg.author == message.author and msg.channel == message.channel
                )
                await answer.delete()
                await prompt.delete()
                if answer:
                    if "yes" not in answer.content:
                        self.verifying[message.guild.id].pop(message.author.id)
                        await channel.send("Deleting responses! Try again.", delete_after=15)
                        return
            except asyncio.TimeoutError:
                self.verifying[message.guild.id].pop(message.author.id)
                await prompt.delete()
                await channel.send("This has been closed due to a timeout", delete_after=15)
                return

        if self.verifying[message.guild.id][message.author.id] is not None:
            # They're done, but not in progress of anything anymore.
            self.verifying[message.guild.id][message.author.id]["step"] = False
            self.verifying[message.guild.id][message.author.id]["done"] = True
            await self.verify_queue(message.author, message.guild)
            self._done_cache.invalidate(self, message.guild.id, message.author.id)
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await channel.send(embed=done, delete_after=15)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = await self.get_verify_config(member.guild.id)
        if settings.active:
            log = settings.log_channel
            await log.send(f":bell: `{member.display_name}` just joined!")

    @commands.group(name="auth", aliases=["ver", "authenticate"])
    @is_verifier_user()
    @commands.guild_only()
    async def auth(self, ctx: commands.Context):
        """
        Allows staff to verify/authorize users.
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Auth Help",
                description="How you can authorize people!",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`list [<PERSON>]`", value="List the people who need verifying in your server.")
            embed.add_field(name="`accept <NAME>`", value="Accept a user")
            embed.add_field(name="`reject <NAME>", value="Reject a user.")
            await ctx.send(embed=embed)

    @auth.command(name="list", usage="[user]")
    @commands.guild_only()
    async def auth_list(self, ctx: commands.Context, *args):
        """
        Lists current users needed to be verified in guild.

        Additionally you can lookup a specific user's ifo using 'list [user]'
        """
        if len(args) >= 1:
            member = ctx.guild.get_member_named(' '.join(args[0:]))
            if member is None:
                await ctx.send("User not found!")
                return
            command = "SELECT data FROM verify_queue WHERE guild_id = {0} and user_id = {1};"
            command = command.format(str(ctx.guild.id), str(member.id))
            async with db.MaybeAcquire() as con:
                con.execute(command)
                row = con.fetchone()
                if row is None:
                    data = None
                else:
                    data = row['data']
            if data is None:
                return await ctx.send("User not found. Have they applied?")
            # data = dab.get_unverified(str(ctx.guild.id), str(member.id))
            message = f"`{member.display_name}` data:"
            for d in data:
                message = message + f"\n{get_key(d, self.names)}: `{data[d]}`"
            await ctx.send(message)
            return

        # unverified = db.get_all_unverified(str(ctx.guild.id))
        command = "SELECT user_id FROM verify_queue WHERE guild_id = {0} ORDER BY user_id;"
        command = command.format(str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
            unverified = con.fetchall()

        if unverified is None or len(unverified) == 0:
            await ctx.send("No people to verify at the moment!")
            return

        message = ""
        for unverify in unverified:
            member: discord.Member = ctx.guild.get_member(int(unverify[0]))
            if member is not None:
                message = message + "\n- " + member.name
            else:
                message = message + "\n- " + unverify[0]
        embed = discord.Embed(
            title="To Verify",
            description=message,
            colour=discord.Colour.dark_purple()
        )
        await ctx.send(embed=embed)

    async def verify_user(self, member: discord.Member, guild: discord.Guild, data):
        # TODO Still use Database() over here a lot...
        dab = Database()
        if guild.id in self.verifying and member.id in self.verifying[guild.id]:
            self.verifying[guild.id].pop(member.id)
        info = {"fields": data}

        command = "DELETE FROM verify_queue WHERE guild_id = $${0}$$ AND user_id = $${1}$$;"
        command = command.format(str(guild.id), str(member.id))
        insert = "INSERT INTO user_data(guild_id, user_id, info) " \
                 "VALUES({0}, {1}, $${2}$$);"
        insert = insert.format(guild.id, member.id, json.dumps(info))

        async with db.MaybeAcquire() as con:
            con.execute(command + "\n" + insert)

        join = ConfigData.join
        messages = join.data["messages"]
        message = random.choice(messages)
        message = message.replace("{user}", member.mention)

        settings = await self.get_verify_config(guild.id)

        welcome: discord.TextChannel = settings.welcome_channel
        if welcome is not None:
            await welcome.send(message)

        if member.dm_channel is None:
            await member.create_dm()
        dm: discord.DMChannel = member.dm_channel

        verify: str = settings.accept_message
        await dm.send(verify)
        await member.remove_roles(settings.unverified_role)
        if "first" in info["fields"]:
            await member.edit(nick=info["fields"]["first"])
        if settings.roles is not None and len(settings.roles) != 0:
            await member.add_roles(*settings.roles)

    async def reject_user(self, member: discord.Member, guild: discord.Guild):
        """
        Rejects a member and sends them DM
        :param member: Member to reject
        :param guild:  Guild that is rejecting
        """
        if guild.id in self.verifying and member.id in self.verifying[guild.id]:
            self.verifying[guild.id].pop(member.id)
        command = "DELETE FROM verify_queue WHERE guild_id = $${0}$$ AND user_id = $${1}$$;"
        command = command.format(str(guild.id), str(member.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)

        self._done_cache.invalidate(self, guild.id, member.id)

        settings = await self.get_verify_config(guild.id)

        if member.dm_channel is None:
            await member.create_dm()
        dm: discord.DMChannel = member.dm_channel

        verify = settings.reject_message
        await dm.send(verify)

    @auth.command(name="accept", usage="<user>")
    @commands.guild_only()
    async def accept(self, ctx: commands.Context, *args):
        """
        Accepts a user into the server.
        """
        if len(args) == 0:
            return await ctx.send_help('auth accept')
        guild: discord.Guild = ctx.guild
        member: discord.Member = guild.get_member_named(' '.join(args[0:]))
        if member is None:
            await ctx.send("User not found!")
        command = "SELECT data FROM verify_queue WHERE guild_id = {0} and user_id = {1};"
        command = command.format(str(guild.id), str(member.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
            if row is None:
                data = None
            else:
                data = row['data']

        if data is None:
            await ctx.send("User not in verify queue")
            return
        await self.verify_user(member, guild, data)

        self._done_cache.invalidate(self, guild.id, member.id)

        settings = await self.get_verify_config(ctx.guild.id)
        log = settings.log_channel
        await log.send(f":bell: {ctx.author.mention} just verified `{member.display_name}`!")

    @auth.command(name="reject", usage="<user>")
    @commands.guild_only()
    async def reject(self, ctx: commands.Context, *args):
        """
        Rejects a user and sends DM
        """
        if len(args) == 0:
            return await ctx.send_help('auth reject')
        guild: discord.Guild = ctx.guild
        member: discord.Member = guild.get_member_named(' '.join(args[0:]))
        if member is None:
            await ctx.send("User not found!")
        command = "SELECT data FROM verify_queue WHERE guild_id = {0} and user_id = {1};"
        command = command.format(str(guild.id), str(member.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
            if row is None:
                user = None
            else:
                user = row['data']
        if user is None:
            await ctx.send("User not in verify queue.")
            return
        await self.reject_user(member, guild)
        settings = await self.get_verify_config(ctx.guild)

        self._done_cache.invalidate(self, guild.id, member.id)

        log = settings.log_channel
        await log.send(f":bell: {ctx.author.mention} just rejected `{member.display_name}`!")


def setup(bot):
    bot.add_cog(Verify(bot))
