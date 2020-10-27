from discord.ext import tasks
from discord.ext.commands import CommandNotFound, MissingPermissions, MissingRole, CommandOnCooldown, CheckFailure, \
    MemberNotFound
import traceback

from cogs import api
from util import storage_cache
from util.discord_util import *
from storage import db
from datetime import datetime, timedelta, timezone
from pytz import timezone

import discord
import random
from util.context import Context
from cogs.help import Help
import os


async def get_prefix(dbot, message: discord.Message):
    user_id = dbot.user.id
    prefixes = ["x>", f"<@{user_id}> ", dbot.user.mention + " "]
    space = ["x> ", f"<@{user_id}> ", dbot.user.mention + " "]
    if message.guild is None:
        prefix = ">"
    else:
        prefix = await dbot.get_guild_prefix(message.guild.id)
        if prefix is None:
            prefix = ">"
    content: str = message.content
    if content.startswith("x> "):
        return space
    if content.startswith(prefix + " "):
        space.append(prefix + " ")
        return space
    prefixes.append(prefix)
    return prefixes


cogs_dir = "cogs"
startup_extensions = [
    "data_commands", "auto_reactions", "qotd", "roles", "verify", "statistics",
    "fun", "utility", "user_settings", "api", "game", "image",
    "random_commands", "text", "guild_config", "command_config", "clip"
]

# bot.remove_command('help')

description = """
A fun utility bot made by DarkKronicle.
"""


def get_time_until():
    zone = timezone('US/Mountain')
    utc = timezone('UTC')
    now = utc.localize(datetime.now())
    now: datetime = now.astimezone(zone)
    minute = 30 - (now.minute % 30)
    delta = timedelta(minutes=minute)
    next_half_hour = (now + delta).replace(microsecond=0, second=0)

    wait_seconds = (next_half_hour - now).seconds
    return wait_seconds


def round_time(dt=None, round_to=30 * 60):
    """Round a datetime object to any time lapse in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   """
    if dt is None:
        zone = timezone('US/Mountain')
        utc = timezone('UTC')
        dt = utc.localize(datetime.now())
        dt = dt.astimezone(zone)

    seconds = (dt.replace(tzinfo=None) - dt.replace(tzinfo=None, hour=0, minute=0, second=0)).seconds
    rounding = (seconds + round_to / 2) // round_to * round_to
    return dt + timedelta(0, rounding - seconds, -dt.microsecond)


class XyloBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix=get_prefix, intents=intents, description=description, case_insensitive=True, owner_id=523605852557672449)
        self.help_command = Help()
        self.spam = commands.CooldownMapping.from_cooldown(10, 15, commands.BucketType.user)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.boot = datetime.now()
        for extension in startup_extensions:
            try:
                self.load_extension(cogs_dir + "." + extension)

            except (discord.ClientException, ModuleNotFoundError):
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()
        self.lines = api.LineCount("DarkKronicle", "XyloBot")

    def run(self):
        super().run(os.getenv('DISCORD_BOT_TOKEN'), reconnect=True, bot=True)

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        self.status.start()
        self.setup_loop.start()
        join = ConfigData.join
        messages = join.data["wakeup"]
        message = random.choice(messages)
        await self.log.send(message)

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            return
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have permission to do that!", delete_after=15)
            return
        if isinstance(error, MissingRole):
            await ctx.send("You don't have permission to do that!", delete_after=15)
            return
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send("Sorry, this command can't be used in private messages.")
        if isinstance(error, CommandOnCooldown):
            message = f"**Hold up** {ctx.author.mention}! You're still on cooldown!"
            await ctx.message.delete()
            await ctx.send(message, delete_after=15)
            return
        if isinstance(error, CheckFailure):
            return
        if isinstance(error, MemberNotFound):
            await ctx.send("Member not found.")
            return
        await super().on_command_error(ctx, error)

    @tasks.loop(hours=1)
    async def status(self):
        """
        Used for setting a random status for the bot.
        """
        act = discord.Activity(name=self.lines.format_random(), type=discord.ActivityType.watching,
                               state="Working Hard")
        await self.change_presence(status=discord.Status.online, activity=act)

    loops = {}

    def add_loop(self, name, function):
        """
        Adds a loop to the thirty minute loop. Needs to take in a function with a parameter time with async.
        """
        self.loops[name] = function

    def remove_loop(self, name):
        """
        Removes a loop based off of a time.
        """
        if name in self.loops:
            self.loops.pop(name)

    @tasks.loop(minutes=30)
    async def time_loop(self):
        time = round_time()
        for loop in self.loops:
            await self.loops[loop](time)

    first_loop = True

    @tasks.loop(seconds=get_time_until())
    async def setup_loop(self):
        # Probably one of the most hacky ways to get a loop to run every thirty minutes based
        # off of starting on one of them.
        if self.first_loop:
            self.first_loop = False
            return
        self.time_loop.start()
        self.setup_loop.stop()

    # https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/bot.py#L190
    # Wow, amazing
    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx: Context = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        cog = self.get_cog("CommandSettings")
        if cog is not None and not await cog.is_command_enabled(ctx):
            # Command is disabled
            return
        await self.invoke(ctx)
        ctx.release()

    @discord.utils.cached_property
    def log(self):
        wh_id = int(os.getenv('WH_ID'))
        wh_token = os.getenv('WH_TOKEN')
        wh = discord.Webhook.partial(id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.session))
        return wh

    async def close(self):
        await super().close()
        await self.session.close()

    async def get_log_channel(self, guild_id):
        util = self.get_cog('Utility')
        if util is None:
            return None
        return await util.get_utility_config(guild_id)

    @storage_cache.cache(maxsize=1024)
    async def get_guild_prefix(self, guild_id):
        command = "SELECT prefix FROM guild_config WHERE guild_id = {};"
        command = command.format(guild_id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
        if row is None:
            return None
        return row['prefix']

    async def send_announcement(self, message):
        command = "SELECT guild_id, announcements FROM guild_config WHERE announcements is NOT NULL;"
        async with db.MaybeAcquire() as con:
            con.execute(command)
            rows = con.fetchall()
        for row in rows:
            guild_id = row['guild_id']
            announcement_id = row['announcements']
            guild = self.get_guild(guild_id)
            if guild is not None:
                channel = guild.get_channel(announcement_id)
                if channel is not None:
                    await channel.send(message)
