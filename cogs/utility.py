import asyncio
import math
from io import StringIO
from json import detect_encoding

import discord
from storage import cache
from storage.database import Database
from util import discord_util
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


class Utility(commands.Cog):
    """
    Commands to make life easier.
    """

    @commands.command(name="invite")
    @commands.guild_only()
    @commands.cooldown(1, 600, commands.BucketType.member)
    async def invite(self, ctx: Context):
        """
        Creates an invite to the server using specific staff settings.
        """
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if "utility" in settings and "invite" in settings["utility"]:
            if settings["utility"]["invite"]["enabled"]:
                channel: discord.TextChannel = ctx.guild.get_channel(settings["utility"]["invite"]["channel"])
                if channel is None:
                    await ctx.send("Error creating invite. Invite channel not found!")
                    return

                invite = await channel.create_invite(max_age=1800)
                if invite is None:
                    await ctx.send("Error creating invite. It just didn't create!")
                    return

                else:
                    await ctx.send(f"Here's your invite link!\n\n{str(invite)}")
                    log = cache.get_log_channel(ctx.guild)
                    if log is not None:
                        embed = discord.Embed(
                            title=f"New Invite Created {str(ctx.author)}: {str(invite)}",
                            description="",
                            timestamp=get_time()
                        )
                        await log.send(embed=embed)
                        # embed.set_footer(text=f"Today at {get_time().strftime('%I:%M $p')}")
                    return

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
        seconds = total_seconds % 60
        minutes = math.floor(total_seconds / 60) % 60
        hours = math.floor(total_seconds / 3600) % 24
        days = math.floor(total_seconds / (3600 * 24))

        return f"{days} Days, {hours} hours, {minutes}, and {seconds} seconds."

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
            for channel in guild.channels():
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
    bot.add_cog(Utility())
