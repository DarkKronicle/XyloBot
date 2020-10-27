import random
from datetime import datetime

from storage import db
from util import checks
from util.context import Context
from util.discord_util import *
from xylo_bot import XyloBot


class QOTD(db.Table):
    guild_id = db.Column(db.Integer(big=True), primary_key=True)
    channel_id = db.Column(db.Integer(big=True))
    time = db.Column(db.String(length=10), default="12:00")


class Channels(commands.Cog):
    """
    Special Channels
    """

    file = ConfigData.questions

    def __init__(self, bot):
        self.bot: XyloBot = bot
        self.bot.add_loop("qotd", self.send_qotd)
        self.questions: list = self.file.data["questions"]
        self.next_question: str = random.choice(self.questions)

    @commands.group(name="!qotd", aliases=["!q"])
    @commands.guild_only()
    @checks.is_mod()
    async def qotd_cmd(self, ctx: Context):
        """
        Commands for Question of the Day
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('!qotd')

    @qotd_cmd.command(name="delete")
    @checks.is_mod()
    @commands.guild_only()
    async def qotd_delete(self, ctx: Context):
        """
        Deletes everything from QOTD
        """
        answer = await ctx.prompt("Are you sure you want to delete QOTD data?")
        if answer is None:
            return await ctx.timeout()
        if not answer:
            return await ctx.send("Not deleting!")
        command = "DELETE FROM qotd WHERE guild_id={0};"
        command = command.format(ctx.guild.id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send("Deleted!")

    @qotd_cmd.command(name="channel")
    @checks.is_mod()
    @commands.guild_only()
    async def qotd_channel(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Set the channel for question for the day.
        """
        if channel is None:
            return await ctx.send("Please specify a correct channel.")
        command = "INSERT INTO qotd(guild_id, channel_id) VALUES ({0}, {1}) ON CONFLICT (guild_id) DO UPDATE SET " \
                  "channel_id = EXCLUDED.channel_id; "
        command = command.format(ctx.guild.id, channel.id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send(f"Channel updated to {channel.mention}")

    @qotd_cmd.command(name="time", usage="<HH:MM>")
    @checks.is_mod()
    @commands.guild_only()
    async def qotd_time(self, ctx: Context, *args):
        """
        Set the time for Question of the Day. Uses 24 hour time format and has to be divisible by 30 minutes.
        """
        if len(args) != 1:
            return await ctx.send("Please specify a correct MST time (and it has to be divisible by 30 minutes). (i.e "
                                  "`15:30`)")
        time = args[0]
        try:
            dt = datetime.strptime(time, '%H:%M')
        except ValueError:
            return await ctx.send("Incorrect time format!")
        if dt.minute != 30 and dt.minute != 0:
            return await ctx.send("Time has to be divisible by 30.")
        command = "INSERT INTO qotd(guild_id, time) VALUES ({0}, $${1}$$) ON CONFLICT (guild_id) DO " \
                  "UPDATE SET " \
                  "time = $$EXCLUDED.time$$;"
        command = command.format(ctx.guild.id, time)
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send(f"Time updated to `{time} MST`.")

    @qotd_cmd.command(name="info")
    @commands.guild_only()
    @checks.is_mod()
    @commands.cooldown(rate=2, per=10, type=commands.BucketType.guild)
    async def qotd_info(self, ctx: Context):
        """
        Sends information about QOTD on your guild.
        """
        command = "SELECT * FROM qotd WHERE guild_id={0};"
        command = command.format(ctx.guild.id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            data = con.fetchone()
        if data is None:
            return await ctx.send("QOTD is not set up on your server.")

        channel = ctx.guild.get_channel(data['channel_id'])
        if channel is None:
            channel = "#deleted-channel"
        else:
            channel = channel.mention
        time = data['time']
        embed = discord.Embed(
            title="Current QOTD Settings",
            description=f"Current Channel: {channel}\nTime: `{time}` MST",
            colour=discord.Colour.purple()
        )
        await ctx.send(embed=embed)

    async def send_qotd(self, time: datetime):
        command = "SELECT * FROM qotd WHERE channel is NOT NULL;"
        async with db.MaybeAcquire() as con:
            con.execute(command)
            rows = con.fetchall()

        embed = discord.Embed(
            title="Question of the Day",
            description=self.next_question,
            colour=discord.Colour.dark_blue()
        )
        for row in rows:
            stime = row['time']
            if stime is None:
                return
            try:
                dt = datetime.strptime(stime, "%H:%M")
            except ValueError:
                continue
            guild = self.bot.get_guild(row['guild_id'])
            if guild is None:
                continue
            channel = guild.get_channel(row['channel_id'])
            if channel is None:
                continue
            if time.hour != dt.hour or time.minute != dt.minute:
                continue
            await channel.send(embed=embed)

        self.queue_next_question()

    def queue_next_question(self):
        self.next_question = random.choice(self.questions)


def setup(bot):
    bot.add_cog(Channels(bot))
