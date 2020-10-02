from discord.ext import tasks
from discord.ext.commands import CommandNotFound, MissingPermissions, MissingRole, CommandOnCooldown, CheckFailure
import traceback
from util.discord_util import *
from storage.database import *
from storage import cache

import discord
from discord.ext.commands import Bot
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


# bot = Bot(command_prefix=get_prefix, intents=intents)
# Command Extensions
# Setup
cogs_dir = "cogs"
startup_extensions = ["data_commands", "help", "auto_reactions", "qotd", "roles", "customization", "verify",
                      "settings", "fun", "utility", "mark"]

# bot.remove_command('help')

description = """
A fun utility bot made by DarkKronicle.
"""


class XyloBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix=get_prefix, intents=intents, description=description)
        # self.remove_command('help')
        self.help_command = Help()
        self.spam = commands.CooldownMapping.from_cooldown(10, 15, commands.BucketType.user)
        for extension in startup_extensions:
            try:
                print(f'trying to load: ' + cogs_dir + "." + extension)
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
        num = random.randint(1, 6)
        if num == 1:
            act = discord.Activity(name="the world burn.", type=discord.ActivityType.watching)
            await self.change_presence(status=discord.Status.dnd, activity=act)
        elif num == 2:
            act = discord.Activity(name="the Marimba.", type=discord.ActivityType.listening)
            await self.change_presence(status=discord.Status.dnd, activity=act)
        elif num == 3:
            act = discord.Activity(name="lets bully Elcinor.", type=discord.ActivityType.playing)
            await self.change_presence(status=discord.Status.dnd, activity=act)
        elif num == 4:
            act = discord.Activity(name="the Terminator.", type=discord.ActivityType.watching)
            await self.change_presence(status=discord.Status.dnd, activity=act)
        elif num == 5:
            act = discord.Activity(name="with flesh bodies.", type=discord.ActivityType.playing)
            await self.change_presence(status=discord.Status.dnd, activity=act)
        elif num == 6:
            act = discord.Activity(name="Elcinor being murdered", type=discord.ActivityType.watching)
            await self.change_presence(status=discord.Status.dnd, activity=act)

    # https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/bot.py#L190
    # Wow, amazing
    async def process_commands(self, message):
        ctx: Context = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        # bucket = self.spam.get_bucket(message)
        # bucket.update_rate_limit(message)

        await self.invoke(ctx)

# def main():
#     # Load extensions for the bot.
#     for extension in startup_extensions:
#         try:
#             print(f'trying to load: ' + cogs_dir + "." + extension)
#             bot.load_extension(cogs_dir + "." + extension)
#             print(f'{extension} has been loaded!')
#
#         except (discord.ClientException, ModuleNotFoundError):
#             print(f'Failed to load extension {extension}.')
#             traceback.print_exc()

    # Load the bot
    # bot.run(, bot=True, reconnect=True)




#
# if __name__ == "__main__":
#     main()
