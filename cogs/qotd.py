from pytz import timezone

from discord.ext import tasks
from discord.ext.commands import Bot
import random
from datetime import datetime, timedelta
from util.discord_util import *
from xylo_bot import XyloBot


class QOTD(commands.Cog):
    """
    Question of the Day
    """
    file = ConfigData.questions
    questions: list = file.data["questions"]
    next_question: str = random.choice(questions)
    go = True
    bot: Bot = None

    def queue_next_question(self):
        self.next_question = random.choice(self.questions)

    @commands.command(name="qotd")
    @commands.guild_only()
    async def qotd(self, ctx: commands.Context, *args):
        if get_role("admin", "rivertron", self.bot) in ctx.author.roles:
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

    async def send_qotd(self, time: datetime):
        if time.hour != 12 and time.minute != 30:
            return
        channel: discord.TextChannel = get_channel("qotd", "rivertron", self.bot)

        if channel is None:
            print("Could not find QOTD channel.")
            return

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

    def __init__(self, bot):
        self.bot: XyloBot = bot
        self.bot.add_loop("qotd", self.send_qotd)


def setup(bot):
    bot.add_cog(QOTD(bot))
