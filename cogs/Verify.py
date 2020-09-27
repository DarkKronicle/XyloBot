import asyncio

from util.DiscordUtil import *
import discord
from util.DiscordUtil import *
from discord.ext import commands
from storage import Cache


def key_or_false(data: dict, key: str):
    if key in data:
        return data[key]
    return False


def get_true(guild):
    field: dict = Cache.get_fields(guild)
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


class Verify(commands.Cog):
    names = {
        "First Name": "first",
        "Last Name": "last",
        "School": "school",
        "Extra Information": "extra",
        "Birthday": "birthday"
    }

    prompts = {
        "first": "What's your first name?",
        "last": "What's your last name?",
        "school": "What school do you go to?",
        "birthday": "What's your birthday? (YYYY-MM-DD)",
        "extra": "What should I know about you?"
    }

    verifying = {}

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def verify_queue(self, member: discord.Member, guild: discord.Guild):
        db = Database()
        settings = db.get_settings(str(guild.id))
        if not check_verification(guild, settings):
            chan: discord.TextChannel = Cache.get_setup_channel(guild)
            await chan.send("Error sending information. Contact staff!", delete_after=15)
            return
        channel = guild.get_channel(int(settings["channels"]["setup-logs"]))
        message = f":bell: `{member.display_name}` just went through the verification process!"
        for field in self.verifying[guild.id][member.id]:
            message = message + f"\n{get_key(field, self.names)}: `{self.verifying[guild.id][member.id]['fields'][field]}`"
        await channel.send(message)

    def is_done(self, member, guild):
        return self.verifying[guild.id][member.id]["done"]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not Cache.get_enabled(message.guild):
            return

        role = Cache.get_unverified_role(message.guild)
        if role not in message.author.roles:
            return

        channel: discord.TextChannel = Cache.get_setup_channel(message.guild)
        if channel is None or message.channel is not channel:
            return

        if message.guild.id not in self.verifying:
            self.verifying[message.guild.id] = {}

        fields = get_true(message.guild)

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

        if self.is_done(message.author, message.guild):
            done = discord.Embed(
                title="Verification Process Complete!",
                description="You're all set! You'll get a DM from me when you get processed.",
                colour=discord.Colour.green()
            )
            await message.delete()
            await channel.send(embed=done, delete_after=15)
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
        print("Joining")
        db = Database()
        settings = db.get_settings(str(member.guild.id))
        if "verification" in settings and "enabled" in settings["verification"] and settings["verification"][
            "enabled"] == True:
            if member.dm_channel is None:
                await member.create_dm()
            dm = member.dm_channel

            setup_channel: discord.TextChannel = member.guild.get_channel(int(settings["channels"]["setup"]))

            # Send message. If there is an extra staff message that will be added.
            content: str = settings["verification"]["join-message"]
            content = content.replace("{server}", member.guild.name)
            content = content.replace("{channel}", setup_channel.mention)

            await dm.send(content)

            log = member.guild.get_channel(int(settings["channels"]["setup-logs"]))
            await log.send(f":bell: `{member.display_name}` just joined!")

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
            embed.add_field(name="`fields`", value="Toggle a verification setting.")
            embed.add_field(name="`toggle`", value="Toggle verification on/off")
            await context.send(embed=embed)

    @verification.command(name="reset")
    async def reset(self, ctx: commands.Context):
        db = Database()
        if db.guild_exists(str(ctx.guild.id)):
            settings = db.get_settings(str(ctx.guild.id))
            settings["verification"] = ConfigData.defaultsettings.data["verification"]
            db.set_settings(str(ctx.guild.id), settings)
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

    @verification.command(name="fields")
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
            if full_setting in self.names:
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
                               "field <SETTING>")
        else:
            await ctx.send("No verification settings found. Please use `verify reset` to reset verification info.")

    @verification.group(name="toggle")
    async def toggle(self, ctx: commands.Context):
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


def setup(bot):
    bot.add_cog(Verify(bot))
