from pytz import timezone

from Config import *
from discord.ext import commands, tasks
from discord.ext.commands import Bot
import random
import discord
from datetime import datetime, timedelta


def get_time_until():
    zone = timezone('US/Mountain')
    utc = timezone('UTC')
    now = utc.localize(datetime.now())
    curtime = now.astimezone(zone)
    return int(round((timedelta(hours=24) - (
                curtime - curtime.replace(hour=13, minute=0, second=0, microsecond=0))).total_seconds() % (24 * 3600)))


class QOTD(commands.Cog):
    file = Config(file="files/questions.json")
    questions: list = file.data["questions"]
    next_question: str = random.choice(questions)
    go = True
    bot: Bot = None

    def queue_next_question(self):
        self.next_question = random.choice(self.questions)

    @commands.command(name="qotd")
    async def qotd(self, ctx: commands.Context, *args):
        if ctx.guild.get_role(731285230249574503) in ctx.author.roles:
            if len(args) < 1:
                error = discord.Embed(
                    title="Not enough arguments.",
                    description="`>qotd <toggle/queue/send/time>`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=error)
                return

            if args[0] == "toggle":
                if self.go:
                    self.go = False
                    embed = discord.Embed(
                        title="QOTD is off!"
                    )
                else:
                    self.go = True
                    embed = discord.Embed(
                        title="QOTD is on!"
                    )
                await ctx.send(embed=embed)
                return

            if args[0] == "queue":
                message = " ".join(args[1:])
                self.next_question = message
                embed = discord.Embed(
                    title="QOTD queued!",
                    description=message,
                    colour=discord.Colour.green()
                )
                await ctx.send(embed=embed)
                return

            if args[0] == "send":
                await self.send_qotd()
                embed = discord.Embed(
                    title="QOTD sent!",
                    colour=discord.Colour.green()
                )
                await ctx.send(embed=embed)
                return

            if args[0] == "time":
                await ctx.send("Time until is " + str(get_time_until()) + " seconds!")
                return

    async def send_qotd(self):
        guild: discord.Guild = self.bot.get_guild(731284440642224139)
        if guild is not None:
            channel: discord.TextChannel = guild.get_channel(756619374944846279)
            message = discord.Embed(
                title="Question of the Day",
                description=self.next_question,
                colour=discord.Colour.dark_blue()
            )
            self.queue_next_question()
            await channel.send(embed=message)

    @tasks.loop(hours=24)
    async def auto_qotd(self):
        if self.go:
            await self.send_qotd()

    setupcomplete = False

    @tasks.loop(count=2, seconds=get_time_until())
    async def setup(self):
        if not self.setupcomplete:
            self.setupcomplete = True
            print("Getting ready!")
            return
        self.auto_qotd.start()

    def __init__(self, bot):
        self.bot = bot
        self.setup.start()


def setup(bot):
    bot.add_cog(QOTD(bot))
