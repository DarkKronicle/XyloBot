import asyncio
import math
from io import StringIO
from json import detect_encoding

import discord
from storage import cache, db
from storage.database import Database
from util import discord_util, storage_cache, checks
from util.context import Context
from util.discord_util import *
from discord.ext import commands
from datetime import datetime, timedelta
from pytz import timezone

from xylo_bot import XyloBot


def get_time():
    zone = timezone('US/Mountain')
    utc = timezone('UTC')
    now = utc.localize(datetime.now())
    curtime = now.astimezone(zone)
    return curtime


class UtilitySettings(db.Table, table_name="utility_settings"):
    guild_id = db.Column(db.Integer(big=True), primary_key=True, index=True)
    invite_channel = db.Column(db.Integer(big=True))
    log_channel = db.Column(db.Integer(big=True))
    join_message = db.Column(db.String(length=2000))


class UtilityConfig:
    __slots__ = ("guild_id", "invite_channel_id", "log_channel_id", "join_message", "config", "bot")

    def __init__(self, bot, guild_id, data):
        self.guild_id = guild_id
        self.bot: XyloBot = bot
        if data is not None:
            self.config = True
            self.invite_channel_id = data['invite_channel']
            self.log_channel_id = data['log_channel']
            self.join_message = data['join_message']
        else:
            self.config = False
            self.invite_channel_id = None
            self.log_channel_id = None
            self.join_message = None

    @property
    def invite_channel(self):
        guild = self.bot.get_guild(self.guild_id)
        return guild.get_channel(self.invite_channel_id)

    @property
    def log_channel(self):
        guild = self.bot.get_guild(self.guild_id)
        return guild.get_channel(self.log_channel_id)


class Utility(commands.Cog):
    """
    Commands to make life easier.
    """

    def __init__(self, bot):
        self.bot: XyloBot = bot

    @storage_cache.cache()
    async def get_utility_config(self, guild_id):
        command = "SELECT * FROM utility_settings WHERE guild_id={};"
        command = command.format(str(guild_id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
        if row is not None:
            row = row[0]

        return UtilityConfig(self.bot, guild_id, row)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = await self.get_utility_config(member.guild.id)
        if settings.join_message is not None:
            if member.dm_channel is None:
                await member.create_dm()
            dm = member.dm_channel

            await dm.send(settings)

    async def insert_blank_config(self, guild_id):
        command = "INSERT INTO utility_settings(guild_id) VALUES ({});"
        command = command.format(str(guild_id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_utility_config.invalidate(self, ctx.guild.id)

    @commands.group(name="!utility", aliases=["!util", "!u"])
    @commands.guild_only()
    @checks.is_mod()
    async def utility(self, ctx: Context):
        """
        Configure utility commands and features.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('!utility')

        settings = await self.get_utility_config(ctx.guild.id)
        if not settings.config:
            await self.insert_blank_config(ctx.guild.id)

    @utility.command(name="current")
    @commands.guild_only()
    @checks.is_mod()
    async def utility_current(self, ctx: Context):
        """
        Lists information about the current utility settings set.
        """
        settings = await self.get_utility_config(ctx.guild.id)
        invite = settings.invite_channel
        log = settings.log_channel
        join_message = settings.join_message

        embed = discord.Embed(
            title="Utility Settings",
            description="All of these can be changed by using the `!utility` command.",
            colour=discord.Colour.purple()
        )
        if log is not None:
            embed.add_field(name="Log Channel", value=f"Logs go to {log.mention}.")
        if invite is not None:
            embed.add_field(name="Invite Channel", value=f"`invite` goes to {invite.mention}.")
        if join_message is not None:
            embed.add_field(name="Join Message DM", value=join_message)

        await ctx.send(embed=embed)

    @utility.command(name="log")
    @commands.guild_only()
    @checks.is_mod()
    async def invite_config(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Sets the log channel for the server.
        """
        if channel is None:
            return await ctx.send("Invalid Text Channel specified.")

        command = "UPDATE utility_settings SET log_channel={0} WHERE guild_id={1};"
        command = command.format(str(ctx.guild.id), str(channel.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)

        await ctx.send(f"Log channel has been set to {channel.mention}!")
        self.get_utility_config.invalidate(self, ctx.guild.id)

    @utility.command(name="invite")
    @commands.guild_only()
    @checks.is_mod()
    async def invite_config(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Set the channel for the invite command.

        If the log channel is setup it will send to there. To disable this just disable the invite command.
        """
        if channel is None:
            return await ctx.send("Invalid Text Channel specified.")

        command = "UPDATE utility_settings SET invite_channel={0} WHERE guild_id={1};"
        command = command.format(str(ctx.guild.id), str(channel.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)

        await ctx.send(f"Invite channel has been set to {channel.mention}!")
        self.get_utility_config.invalidate(self, ctx.guild.id)

    @utility.command(name="join")
    @commands.guild_only()
    @checks.is_mod()
    async def join(self, ctx: Context):
        """
        Configure what message should be sent to a member on join?
        """
        answer = await ctx.ask('What message should I send to a new member on join? (Use `none` if you want to disable it.)')
        if answer is None:
            await ctx.timeout()

        self.get_utility_config.invalidate(self, ctx.guild.id)

        if answer == False:
            command = "UPDATE utility_settings SET join_message=NULL WHERE guild_id={0};"
            command = command.format(str(ctx.guild.id))
            async with db.MaybeAcquire() as con:
                con.execute(command)
            return ctx.send("On join message disabled!")

        answer = answer.replace("$", "\\$")
        command = "UPDATE utility_settings SET join_message=$${0}$$ WHERE guild_id={1};"
        command = command.format(answer, str(ctx.guild.id))
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send(f"On join message set to:\n\n{answer}")

    @commands.command(name="invite")
    @commands.guild_only()
    @commands.cooldown(1, 600, commands.BucketType.member)
    async def invite(self, ctx: Context):
        """
        Creates an invite to the server using specific staff settings.
        """
        settings = await self.get_utility_config(ctx.guild.id)
        if settings.invite_channel is not None:
            channel: discord.TextChannel = settings.invite_channel

            invite = await channel.create_invite(max_age=1800)
            if invite is None:
                await ctx.send("Error creating invite. It just didn't create!")
                return

            else:
                await ctx.send(f"Here's your invite link!\n\n{str(invite)}")
                log = settings.log_channel
                if log is not None:
                    embed = discord.Embed(
                        title=f"New Invite Created {str(ctx.author)}: {str(invite)}",
                        description="",
                        timestamp=get_time()
                    )
                    await log.send(embed=embed)
                return
        else:
            await ctx.send("No invite channel setup!")

    @commands.command(name="dmme")
    async def dmme(self, ctx: Context):
        dm = await ctx.get_dm()
        await dm.send("Hello there!")

    @commands.command(name="ping")
    async def ping(self, ctx: Context):
        time0 = ctx.message.created_at.microsecond / 1000
        sent = await ctx.send("Pinging")
        time1 = sent.created_at.microsecond / 1000
        await asyncio.sleep(0.5)
        await sent.edit(content="Pinging.")
        await asyncio.sleep(0.5)
        await sent.edit(content="Pinging..")
        await asyncio.sleep(0.5)
        await sent.edit(content="Pinging...")
        await asyncio.sleep(0.5)
        dif1 = time1 - time0
        await sent.edit(content=f"Pong! Pinging time was {dif1}ms")

    @commands.command(name="grade")
    async def grade(self, ctx: Context, *args):
        """
        Calculates your grade based off of categories.

        Format each arg like CURRENT|OUTOF|WEIGHT.
        """
        if len(args) == 0:
            await ctx.send("Make sure to put in grades like this: `grade CURRENT|OUTOF|WEIGHT CURRENT...`")
            return
        if len(args) > 25:
            return await ctx.send("Too many grades ;-;")
        grades = []
        total = []
        for arg in args:
            content = arg.split("|")
            if len(content) != 3:
                return await ctx.send("Argument should be: `CURRENT|OUTOF|WEIGHT`")

            try:
                current = float(content[0])
                outof = float(content[1])
                weight = float(content[2]) / 100
                percent = float(current / outof)
            except ValueError:
                return await ctx.send(
                    f"Could not parse arguments for integers. Args were: `f{content[0]} f{content[1]} f{content[2]}")

            grade = {
                "current": current,
                "outof": outof,
                "weight": weight,
                "percent": percent,
                "weighted": percent * weight
            }
            grades.append(grade)
            total.append(percent * weight)

        totalpercent = 0.0
        for tot in total:
            totalpercent = totalpercent + tot
        embed = discord.Embed(
            colour=discord.Colour.gold()
        )
        message = f"**Normal Grading:** {str(round(totalpercent * 100, 2))}%\n**Standard Based:** {str(round(totalpercent * 4, 2))}\n\n```Percentage | Weighted -=- Current/Total\n"
        for grade in grades:
            message = message + f"\n{str(round(grade['percent'] * 100, 2))}% | {str(round(grade['weighted'] * 100))}% " \
                                f"-=- {str(grade['current'])}/{str(grade['outof'])} "
        message = message + "```"
        embed.description = message
        await ctx.send(embed=embed)

    @commands.command(name="json")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def basic_json(self, ctx: Context, *args):
        """
        Creates a JSON file based off of your arguments. Split with a |
        """

        if len(args) == 0:
            return await ctx.send(
                "Make sure to add arguments with | dividing key from value. Like `>json 'KEY|VALUE' 'KEY|VALUE'...`")

        questions = {}
        message = "Building your file...\n\n```Question | Answer\n-----"
        for arg in args:
            split = arg.split("|")
            if len(split) == 1:
                return await ctx.send("Make sure that a | divides your answer from your question.")
            questions[split[0]] = split[1]
            message = message + f"\n{split[0]} | {split[1]}"

        message = message + "```"

        buffer = StringIO()
        json.dump(questions, fp=buffer, indent=4)
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="quiz.json")
        await ctx.send(message, file=file)

    @commands.command(name="txt")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def txt(self, ctx: Context, *args):
        """
        Generates a text file based on what you put.
        """
        if len(args) == 0:
            data = ctx.ask("What do you want in the file?")
            if data is None:
                await ctx.timeout()
        else:
            data = ' '.join(args)
        buffer = StringIO()
        buffer.write(data)
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="file.txt")
        await ctx.send("*Bing bada boom!* Here's your file!", file=file)

    @commands.command(name="paste", usage="[FORMAT]")
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def paste(self, ctx: Context):
        """
        Sends the content of a file you send.

        You can specifiy an argument for formatting. Like JAVA, PYTHON, RUBY...
        """
        if len(ctx.message.attachments) != 1:
            return await ctx.send("Please attach ***one*** file to the message!")

        atta: discord.Attachment = ctx.message.attachments[0]
        name: str = atta.filename
        types = {".py": "PYTHON", ".json": "JSON", ".txt": "", ".xml": "XML", ".md": "", ".yml": "YAML"}
        file_type = None
        for t in types:
            if name.endswith(t):
                file_type = types[t]
                break
        if file_type is None:
            return await ctx.send("Please use a proper image format.")

        buffer = await discord_util.get_data_from_url(atta.url)
        if buffer is None:
            return await ctx.send("Something went wrong getting that file...")

        data = buffer.read()
        if isinstance(data, str):
            if data.startswith('\ufeff'):
                return await ctx.send("Something went wrong with loading that file...")
        else:
            if not isinstance(data, (bytes, bytearray)):
                return await ctx.send("Something went wrong opening up that file...")
            data = data.decode(detect_encoding(data), 'surrogatepass')

        if len(data) > 1990:
            return await ctx.send("File too big!")
        message = f"```{file_type}\n{data}\n```"
        await ctx.send(message)

    def get_time_up(self, bot):
        now = datetime.now()
        now.replace(microsecond=0)
        boot = bot.boot
        boot.replace(microsecond=0)
        dif: timedelta = now - boot

        total_seconds = dif.total_seconds()
        seconds = math.floor(total_seconds % 60)
        minutes = math.floor(total_seconds / 60) % 60
        hours = math.floor(total_seconds / 3600) % 24
        days = math.floor(total_seconds / (3600 * 24))

        return f"{days} Days, {hours} hours, {minutes} minutes, and {seconds} seconds."

    @commands.command(name="uptime")
    async def uptime(self, ctx: Context):
        embed = discord.Embed(
            description="I have been up for " + self.get_time_up(ctx.bot),
            colour=discord.Colour.purple()
        )
        embed.set_author(name="Current Up Time")
        await ctx.send(embed=embed)

    @commands.command(name="about")
    async def about(self, ctx):
        """
        Info about the bot.
        """

        bot: XyloBot = ctx.bot

        users = 0
        unique_users = len(ctx.bot.users)
        text = 0
        voice = 0
        guilds = 0

        uptime = self.get_time_up(ctx.bot)

        for guild in bot.guilds:
            guild: discord.Guild
            guilds = guilds + 1
            users = users + guild.member_count
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text = text + 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice = voice + 1

        embed = discord.Embed(
            title="Current Stats",
            colour=discord.Colour.purple()
        )
        owner = bot.get_user(bot.owner_id)
        embed.set_author(name=str(owner), icon_url=owner.avatar_url)
        message = f"Guilds: `{guilds}`\nUsers: `{users}` Unique: `{unique_users}`\n\nText Channels: `{text}`\nVoice Channels: `{voice}`\n\nUptime: `{uptime}`"
        embed.description = message
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
