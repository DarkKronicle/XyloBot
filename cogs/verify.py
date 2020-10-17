import asyncio
import random

from storage.db import MaybeAcquire
from util import storage_cache, checks
from util.context import Context
from util.discord_util import *
from discord.ext import commands
from storage import cache, db
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


def get_true(guild):
    field: dict = cache.get_fields(guild)
    if field is None:
        return None
    for f in list(field):
        if not field[f]:
            field.pop(f)
    return field


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
        if not checks.is_channel(ctx, settings.setup_channel):
            return False
        return await checks.check_permissions(ctx, {"send_messages": True})

    return commands.check(predicate)


class VerifySettings(db.Table, table_name="verify_settings"):
    guild_id = db.Column(db.Integer(big=True), index=True)

    setup_channel = db.Column(db.Integer(big=True))
    setup_log = db.Column(db.Integer(big=True))

    unverified_role = db.Column(db.Integer(big=True))
    roles = db.Column(db.JSON())

    fields = db.Column(db.JSON())
    active = db.Column(db.Boolean(), default=True)


class VerifyQueue(db.Table, table_name="verify_queue"):
    guild_id = db.Column(db.Integer(big=True), primary_key=True)
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    data = db.Column(db.JSON())

    @classmethod
    def create_table(cls, *, overwrite=False):
        statement = super().create_table(overwrite=overwrite)
        # create the unique index
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS verify_queue_uniq_idx ON verify_queue (guild_id, user_id);"
        return statement + '\n' + sql


class VerifyConfig:
    __slots__ = (
        "bot", "guild_id", "setup_channel_id", "setup_log_id", "unverified_role_id", "roles_data", "fields", "active")

    def __init__(self, *, guild_id, bot, data=None):
        self.guild_id = guild_id
        self.bot: XyloBot = bot

        if data is not None:
            # self.active = data['active']
            # self.setup_channel_id = data['setup_channel']
            # self.setup_log_id = data['setup_log']
            # self.fields = data['fields']['fields']
            # self.unverified_role_id = data['unverified_role']
            # self.roles_data = data['roles']['roles']
            self.setup_channel_id = data[0]
            self.setup_log_id = data[1]
            self.unverified_role_id = data[2]
            self.roles_data = data[3]['roles']
            self.fields = data[4]
            self.active = data[5]
        else:
            self.active = False
            self.setup_channel_id = None
            self.setup_log_id = None
            self.fields = None
            self.unverified_role_id = None
            self.roles_data = None

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
        if settings.setup_channel_id is not None:
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

        command = "INSERT INTO verify_settings(guild_id, setup_channel, setup_log, unverified_role, roles, fields, " \
                  "active) VALUES({0}, {1}, {2}, {3}, $${4}$$, $${5}$$, {6}); "
        command = command.format(str(ctx.guild.id), str(channel.id), str(log.id), str(unverified.id),
                                 json.dumps(roles_dict), json.dumps(fields), "TRUE")
        with db.MaybeAcquire() as con:
            con.execute(command)

        await ctx.send("You're all setup!")

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
        with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(ctx.guild.id)
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
        with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_verify_config.invalidate(ctx.guild.id)
        await ctx.send("All data has been deleted from this server.")

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
        if active:
            active_str = "Enabled"
        else:
            active_str = "Disabled"
        message = "Current Verification settings. Edit with `>help !verify` commands.\n\nCurrent fields enabled:\n```"
        for field in fields:
            name = get_key(field, self.names)
            message = message + f"{name}\n"
        message = message + f"```\nSetup Channel - {setup_channel.mention}\nSetup Log Channel - {setup_log.mention}\n" \
                            f"Unverified Role - {unverified_role.name}\n\nRoles on verification:"
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
        command = "SELECT setup_channel, setup_log, unverified_role, roles, fields, active FROM verify_settings WHERE guild_id={}"
        command = command.format(str(guild_id))
        with MaybeAcquire(connection=connection) as con:
            con.execute(command)
            data = con.fetchone()
        return VerifyConfig(guild_id=guild_id, bot=self.bot, data=data)

    verifying = {}

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def verify_queue(self, member: discord.Member, guild: discord.Guild):
        dab = Database()
        settings = dab.get_settings(str(guild.id))
        command = "INSERT INTO verify_queue(guild_id, user_id, data) " \
                  "VALUES($${0}$$, $${1}$$, $${2}$$);"
        command = command.format(str(guild.id), str(member.id),
                                 json.dumps(self.verifying[guild.id][member.id]['fields']))
        with db.MaybeAcquire() as con:
            con.execute(command)

        if not check_verification(guild, settings):
            chan: discord.TextChannel = cache.get_setup_channel(guild)
            await chan.send("Error sending information. Contact staff!", delete_after=15)
            return

        channel = guild.get_channel(int(settings["channels"]["setup-logs"]))
        message = f":bell: `{member.display_name}` just went through the verification process!"
        for field in self.verifying[guild.id][member.id]['fields']:
            message = message + f"\n-    {get_key(field, self.names)}: `{self.verifying[guild.id][member.id]['fields'][field]}`"
        await channel.send(message)

    def is_done(self, member, guild):
        if guild.id in self.verifying and member.id in self.verifying[guild.id]:
            return self.verifying[guild.id][member.id]["done"]
        else:
            db = Database()
            info = db.get_unverified(str(guild.id), str(member.id))
            if info is not None:
                return True
            return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not cache.get_enabled(message.guild):
            return

        role = cache.get_unverified_role(message.guild)
        if role not in message.author.roles:
            return

        channel: discord.TextChannel = cache.get_setup_channel(message.guild)
        if channel is None or message.channel is not channel:
            return

        if message.guild.id not in self.verifying:
            self.verifying[message.guild.id] = {}

        fields = get_true(message.guild)

        if self.is_done(message.author, message.guild):
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await message.delete()
            await channel.send(embed=done, delete_after=15)
            return

        if message.author.id in self.verifying[message.guild.id]:
            current = self.verifying[message.guild.id][message.author.id]
        else:
            self.verifying[message.guild.id][message.author.id] = {
                "step": 0,
                "done": False,
                "fields": {}
            }
            current = self.verifying[message.guild.id][message.author.id]

        if current["step"] > 0:
            return

        if len(fields) == 0:
            await message.delete()
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await channel.send(embed=done, delete_after=15)
            await self.verify_queue(message.author, message.guild)
            return

        await message.delete()
        self.verifying[message.guild.id][message.author.id]["step"] = 1
        for value in fields:
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
            self.verifying[message.guild.id][message.author.id]["step"] = 0
            self.verifying[message.guild.id][message.author.id]["done"] = True
            await self.verify_queue(message.author, message.guild)
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await channel.send(embed=done, delete_after=15)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        db = Database()
        db.add_new_user(str(member.id))
        settings = db.get_settings(str(member.guild.id))
        if "verification" in settings and "enabled" in settings["verification"] and settings["verification"][
            "enabled"]:
            if member.dm_channel is None:
                await member.create_dm()
            dm = member.dm_channel

            setup_channel: discord.TextChannel = member.guild.get_channel(int(settings["channels"]["setup"]))

            # Send message. If there is an extra staff message that will be added.
            content: str = settings["messages"]["join-message"]
            content = content.replace("{server}", member.guild.name)
            content = content.replace("{channel}", setup_channel.mention)

            await dm.send(content)
            await member.add_roles(cache.get_unverified_role(member.guild))

            log = member.guild.get_channel(int(settings["channels"]["setup-logs"]))
            await log.send(f":bell: `{member.display_name}` just joined!")

    @commands.group(name="verification")
    @is_verifier_user()
    async def verification(self, context):
        """
        Customizes verification on the server.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                title="Verification Help",
                description="View commands for verification.",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`info`", value="View what verification settings are enabled.")
            embed.add_field(name="`reset`", value="Reset verification information for your server.")
            embed.add_field(name="`fields`", value="Toggle a verification setting.")
            embed.add_field(name="`toggle`", value="Toggle verification on/off")
            embed.add_field(name="`role`", value="Roles to give when verified")
            await context.send(embed=embed)

    @verification.command(name="reset")
    @commands.guild_only()
    async def reset(self, ctx: commands.Context):
        """
        Reset current verification settings to default.
        """
        db = Database()
        if db.guild_exists(str(ctx.guild.id)):
            settings = db.get_settings(str(ctx.guild.id))
            settings["verification"] = ConfigData.defaultsettings.data["verification"]
            db.set_settings(str(ctx.guild.id), settings)
        else:
            db.default_settings(str(ctx.guild.id))
        await ctx.send("Reset verification information!")

    @verification.command(name="info")
    @commands.guild_only()
    async def info(self, ctx: commands.Context):
        """
        Gets current information on the verification process.

        Shows what is enabled and what is not. If no settings are there, it is created.
        """
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if settings is None:
            db.default_settings(str(ctx.guild.id))
            await ctx.send("You didn't have settings. Creating now.")
        if "verification" in settings and "fields" in settings["verification"]:
            info = discord.Embed(
                title="Information",
                description="What you have enabled.",
                colour=discord.Colour.purple()
            )
            settings = settings["verification"]["fields"]
            info.add_field(name="Enabled", value=str(key_or_false(settings, "enabled")))
            info.add_field(name="First Name", value=str(key_or_false(settings, "first")))
            info.add_field(name="Last Name", value=str(key_or_false(settings, "last")))
            info.add_field(name="School", value=str(key_or_false(settings, "school")))
            info.add_field(name="Extra Information", value=str(key_or_false(settings, "extra")))
            info.add_field(name="Birthday", value=str(key_or_false(settings, "birthday")))
            await ctx.send(embed=info)

        else:
            await ctx.send(
                "No verification settings found. Please use `verification reset` to reset verification info.")

    @verification.command(name="fields", usage="<setting> <value>")
    @commands.guild_only()
    async def fields(self, ctx: commands.Context, *args):
        if len(args) == 0:
            error = discord.Embed(
                title="Incorrect Usage",
                description="`>verification field <SETTING>`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=error)
            return
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if "verification" in settings and "fields" in settings["verification"]:
            full_setting = ' '.join(args[0:]).lower()
            name = []
            for sets in self.names:
                name.append(sets.lower())
            if full_setting in name:
                setting = self.names[full_setting]
                if setting in settings["verification"]["fields"]:
                    enabled = settings["verification"]["fields"][setting]
                else:
                    enabled = False
                settings["verification"]["fields"][setting] = not enabled
                db.set_settings(str(ctx.guild.id), settings)
                if enabled:
                    await ctx.send(f"Toggling off {args[0]}.")
                else:
                    await ctx.send(f"Toggling on {args[0]}.")
            else:
                await ctx.send("No setting found by that name. Look through `>verification info`. `>verification "
                               "field <SETTING>`")
        else:
            await ctx.send("No verification settings found. Please use `verify reset` to reset verification info.")

    @verification.group(name="role", usage="<current|reset|add|remove>")
    async def role(self, ctx: commands.Context, *args):
        """
        Configure what roles will be added on verify.

        Make sure that the roles are BELOW Xylo's role.
        """
        if len(args) == 0:
            error = discord.Embed(
                title="Role Help",
                description="`role <current/add/remove/reset> <role>",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=error)
            return
        db = Database()

        if args[0] == "current":
            settings = db.get_settings(str(ctx.guild.id))
            if "roles" not in settings["verification"] or len(settings["verification"]["roles"]) == 0:
                await ctx.send("No roles currently setup.")
                return

            message = "Current roles:"
            for role in settings["verification"]["roles"]:
                r = ctx.guild.get_role(role)
                if r is not None:
                    message = message + f"-   `{r.name}`"
                else:
                    message = message + f"-   `{str(role)}`"

            await ctx.send(message)
            return

        if args[0] == "reset":
            settings = db.get_settings(str(ctx.guild.id))
            settings["verification"]["roles"] = []
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send("Roles cleared!")
            return

        try:
            role: discord.Role = ctx.guild.get_role(int(args[1]))
        except ValueError:
            await ctx.send("Provide the Role ID for the `<role>` argument.")
            return

        if role is None:
            await ctx.send("Role not found.")
            return

        if args[0] == "add":
            if len(args) == 1:
                await ctx.send("Not enough arguments!")
                return
            settings = db.get_settings(str(ctx.guild.id))
            if "roles" not in settings["verification"]:
                settings["verification"]["roles"] = []
            settings["verification"]["roles"].append(role.id)
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send(f"`{role.name}` added!")
            return

        if args[0] == "remove":
            if len(args) == 1:
                await ctx.send("Not enough arguments!")
                return
            settings = db.get_settings(str(ctx.guild.id))
            if "roles" not in settings["verification"]:
                settings["roles"] = []
            if role.id in settings["verification"]["roles"]:
                settings["verification"]["roles"].remove(role.id)
            else:
                await ctx.send(f"`{role.name}` not found in role settings!")
                return
            db.set_settings(str(ctx.guild.id), settings)
            await ctx.send(f"`{role.name}` removed!")
            return

        error = discord.Embed(
            title="Command not found",
            description="`role <add/remove/reset> <role>",
            colour=discord.Colour.purple()
        )
        await ctx.send(embed=error)
        return

    @verification.group(name="toggle", usage="<field>")
    async def toggle(self, ctx: commands.Context):
        """
        Toggles a specific verification field.
        """
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if not set_check_verification(ctx.guild):
            await ctx.send("You need to setup the channels `setup` and `setup-logs` before you can "
                           "enable! `>settings channel`")
            return

        if "verification" in settings:
            enabled = key_or_false(settings["verification"], "enabled")
            settings["verification"]["enabled"] = not enabled
            if enabled:
                await ctx.send("Turning off verification!")
            else:
                await ctx.send("Turning on verification!")
            db.set_settings(str(ctx.guild.id), settings)
        else:
            await ctx.send("No verification settings found. Please use `verify reset` to reset verification info.")

    @commands.group(name="auth", aliases=["verify", "authenticate"])
    @is_verifier_user()
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
        dab = Database()
        if len(args) >= 1:
            member = ctx.guild.get_member_named(' '.join(args[0:]))
            if member is None:
                await ctx.send("User not found!")
                return
            command = "SELECT data FROM verify_queue WHERE guild_id = $${0}$$ and user_id = $${1}$$;"
            command = command.format(str(ctx.guild.id), str(member.id))
            with db.MaybeAcquire() as con:
                con.execute(command)
                row = con.fetchone()
                if row is None:
                    data = None
                else:
                    data = row[0]
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
        with db.MaybeAcquire() as con:
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
        dab = Database()
        if guild.id in self.verifying and member.id in self.verifying[guild.id]:
            self.verifying[guild.id].pop(member.id)
        info = {"fields": data}

        command = "DELETE FROM verify_queue WHERE guild_id = $${0}$$ AND user_id = $${1}$$;"
        command = command.format(str(guild.id), str(member.id))
        with db.MaybeAcquire() as con:
            con.execute(command)
        # dab.delete_unverified(str(guild.id), str(member.id))
        dab.add_user(info, str(member.id), str(guild.id))

        join = ConfigData.join
        messages = join.data["messages"]
        message = random.choice(messages)
        message = message.replace("{user}", member.mention)

        settings = dab.get_settings(str(guild.id))

        welcome: discord.TextChannel = guild.get_channel(int(settings["channels"]["welcome"]))
        await welcome.send(message)

        if member.dm_channel is None:
            await member.create_dm()
        dm: discord.DMChannel = member.dm_channel

        verify: str = settings["messages"]["verify-message"]
        verify = verify.replace("{server}", guild.name)
        await dm.send(verify)
        await member.remove_roles(cache.get_unverified_role(guild))
        if "first" in info["fields"]:
            await member.edit(nick=info["fields"]["first"])
        if "roles" in settings["verification"] and len(settings["verification"]["roles"]) != 0:
            roles = []
            for role in settings["verification"]["roles"]:
                r = guild.get_role(role)
                if r is not None:
                    roles.append(r)
            if len(roles) > 0:
                await member.add_roles(*roles)

    async def reject_user(self, member: discord.Member, guild: discord.Guild):
        """
        Rejects a member and sends them DM
        :param member: Member to reject
        :param guild:  Guild that is rejecting
        """
        dab = Database()
        if guild.id in self.verifying and member.id in self.verifying[guild.id]:
            self.verifying[guild.id].pop(member.id)
        command = "DELETE FROM verify_queue WHERE guild_id = $${0}$$ AND user_id = $${1}$$;"
        command = command.format(str(guild.id), str(member.id))
        with db.MaybeAcquire() as con:
            con.execute(command)
        # db.delete_unverified(str(guild.id), str(member.id))
        settings = dab.get_settings(str(guild.id))

        if member.dm_channel is None:
            await member.create_dm()
        dm: discord.DMChannel = member.dm_channel

        verify: str = settings["messages"]["reject-message"]
        verify = verify.replace("{server}", guild.name)
        # if message is not None:
        #     verify = verify + "\n\nStaff message: " + message
        await dm.send(verify)

    @auth.command(name="accept", usage="<user>")
    @commands.guild_only()
    async def accept(self, ctx: commands.Context, *args):
        """
        Accepts a user into the server.
        """
        if len(args) == 0:
            embed = discord.Embed(
                title="Auth Accept",
                description="`>auth accept <NAME>`",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)
            return
        guild: discord.Guild = ctx.guild
        member: discord.Member = guild.get_member_named(' '.join(args[0:]))
        if member is None:
            await ctx.send("User not found!")
        # db = Database()
        # user = db.get_unverified(str(guild.id), str(member.id))
        command = "SELECT data FROM verify_queue WHERE guild_id = $${0}$$ and user_id = $${1}$$;"
        with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
            if row is None:
                user = None
            else:
                user = row[0]
        if user is None:
            await ctx.send("User not in verify queue")
            return
        await self.verify_user(member, guild, user)
        log = cache.get_setup_log_channel(ctx.guild)
        await log.send(f":bell: {ctx.author.mention} just verified `{member.display_name}`!")

    @auth.command(name="reject", usage="<user>")
    @commands.guild_only()
    async def reject(self, ctx: commands.Context, *args):
        """
        Rejects a user and sends DM
        """
        if len(args) == 0:
            embed = discord.Embed(
                title="Auth Accept",
                description="`>auth reject <NAME>`",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)
            return
        guild: discord.Guild = ctx.guild
        member: discord.Member = guild.get_member_named(' '.join(args[0:]))
        if member is None:
            await ctx.send("User not found!")
        # db = Database()
        # user = db.get_unverified(str(guild.id), str(member.id))
        command = "SELECT data FROM verify_queue WHERE guild_id = $${0}$$ and user_id = $${1}$$;"
        with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
            if row is None:
                user = None
            else:
                user = row[0]
        if user is None:
            await ctx.send("User not in verify queue")
            return
        await self.reject_user(member, guild)
        log = cache.get_setup_log_channel(ctx.guild)
        await log.send(f":bell: {ctx.author.mention} just rejected `{member.display_name}`!")


def setup(bot):
    bot.add_cog(Verify(bot))
