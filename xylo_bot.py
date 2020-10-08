from discord.ext import tasks
from discord.ext.commands import CommandNotFound, MissingPermissions, MissingRole, CommandOnCooldown, CheckFailure
import traceback
from util.discord_util import *
from storage.database import *
from storage import cache
from datetime import datetime, timedelta, timezone
from pytz import timezone

import discord
import random
from util.context import Context
from cogs.help import Help


def get_prefix(dbot, message: discord.Message):
    user_id = dbot.user.id
    prefixes = ["x>", f"<@{user_id}> "]
    space = ["x> ", f"<@{user_id}> "]
    if message.guild is None:
        return prefixes
    prefix = cache.get_prefix(message.guild)
    if prefix is not None:
        content: str = message.content
        if content.startswith("x> "):
            return space
        if content.startswith(prefix + " "):
            space.append(prefix + " ")
            return space
        prefixes.append(prefix)
    return prefixes


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


# bot = Bot(command_prefix=get_prefix, intents=intents)
# Command Extensions
# Setup
cogs_dir = "cogs"
startup_extensions = ["data_commands", "auto_reactions", "qotd", "roles", "verify", "statistics",
                      "settings", "fun", "utility", "mark", "user_settings", "api", "games.game", "image"]

# bot.remove_command('help')

description = """
A fun utility bot made by DarkKronicle.
"""


def get_time_until():
    zone = timezone('US/Mountain')
    utc = timezone('UTC')
    now = utc.localize(datetime.now())
    now = now.astimezone(zone)
    delta = timedelta(minutes=30)
    next_half_hour = (now + delta).replace(microsecond=0, second=0, hour=0)

    wait_seconds = (next_half_hour - now).seconds
    return wait_seconds


class XyloBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix=get_prefix, intents=intents, description=description, case_insensitive=True)
        # self.remove_command('help')
        self.help_command = Help()
        self.spam = commands.CooldownMapping.from_cooldown(10, 15, commands.BucketType.user)
        for extension in startup_extensions:
            try:
                self.load_extension(cogs_dir + "." + extension)
                print(f'{extension} has been loaded!')

            except (discord.ClientException, ModuleNotFoundError):
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()

    def run(self):
        super().run(os.getenv('DISCORD_BOT_TOKEN'), reconnect=True, bot=True)

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        self.status.start()
        self.setup_loop.start()
        update = get_channel("xylo-updates", "rivertron", self)
        join = ConfigData.join
        messages = join.data["wakeup"]
        message = random.choice(messages)
        await update.send(message)

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            return
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have permission to do that!", delete_after=15)
            return
        if isinstance(error, MissingRole):
            await ctx.send("You don't have permission to do that!", delete_after=15)
            return
        if isinstance(error, CommandOnCooldown):
            message = f"**Hold up** {ctx.author.mention}! You're still on cooldown!"
            await ctx.message.delete()
            await ctx.send(message, delete_after=15)
            return
        if isinstance(error, CheckFailure):
            return
        raise error

    @tasks.loop(hours=1)
    async def status(self):
        """
        Used for setting a random status for the bot.
        """
        num = random.randint(1, 4)
        if num == 1:
            act = discord.Activity(name="the world burn.", type=discord.ActivityType.watching)
            await self.change_presence(status=discord.Status.online, activity=act)
        elif num == 2:
            act = discord.Activity(name="the Marimba.", type=discord.ActivityType.listening)
            await self.change_presence(status=discord.Status.online, activity=act)
        elif num == 3:
            act = discord.Activity(name="lets bully Elcinor.", type=discord.ActivityType.playing)
            await self.change_presence(status=discord.Status.online, activity=act)
        elif num == 4:
            act = discord.Activity(name="the Terminator.", type=discord.ActivityType.watching)
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
        ctx: Context = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)
