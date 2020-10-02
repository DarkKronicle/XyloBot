import argparse
import logging
from discord.ext import tasks
from discord.ext.commands import CommandNotFound, MissingPermissions, MissingRole, CommandOnCooldown, CheckFailure
import traceback
from util.discord_util import *
from storage.database import *
from storage import cache

import discord
from discord.ext.commands import Bot
import random

intents = discord.Intents.default()
intents.members = True


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


bot = Bot(command_prefix=get_prefix, intents=intents)

# We create our own in cogs/help.py
bot.remove_command('help')

# Command Extensions
# Setup
startup_extensions = ["data_commands", "help", "auto_reactions", "qotd", "roles", "customization", "verify",
                      "settings", "fun", "utility", "mark"]

# Extension directory
cogs_dir = "cogs"


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    status.start()
    update = get_channel("xylo-updates", "rivertron", bot)
    join = ConfigData.join
    messages = join.data["wakeup"]
    message = random.choice(messages)
    await update.send(message)


@bot.event
async def on_command_error(ctx: commands.Context, error):
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
async def status():
    """
    Used for setting a random status for the bot.
    """
    num = random.randint(1, 6)
    if num == 1:
        act = discord.Activity(name="the world burn.", type=discord.ActivityType.watching)
        await bot.change_presence(status=discord.Status.dnd, activity=act)
    elif num == 2:
        act = discord.Activity(name="the Marimba.", type=discord.ActivityType.listening)
        await bot.change_presence(status=discord.Status.dnd, activity=act)
    elif num == 3:
        act = discord.Activity(name="lets bully Elcinor.", type=discord.ActivityType.playing)
        await bot.change_presence(status=discord.Status.dnd, activity=act)
    elif num == 4:
        act = discord.Activity(name="the Terminator.", type=discord.ActivityType.watching)
        await bot.change_presence(status=discord.Status.dnd, activity=act)
    elif num == 5:
        act = discord.Activity(name="with flesh bodies.", type=discord.ActivityType.playing)
        await bot.change_presence(status=discord.Status.dnd, activity=act)
    elif num == 6:
        act = discord.Activity(name="Elcinor being murdered", type=discord.ActivityType.watching)
        await bot.change_presence(status=discord.Status.dnd, activity=act)


def main():
    # Load extensions for the bot.
    for extension in startup_extensions:
        try:
            print(f'trying to load: ' + cogs_dir + "." + extension)
            bot.load_extension(cogs_dir + "." + extension)
            print(f'{extension} has been loaded!')

        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

    # Load the bot
    bot.run(os.getenv('DISCORD_BOT_TOKEN'), bot=True, reconnect=True)


def _cli():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    # parser.add_argument('config_file', help="Which config file to use",
    #                     default="configs.json")
    # ADD OTHER VARIABLES BELOW THIS LINE
    parser.add_argument('-d', '--debug', help="Pring debuggin information",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.ERROR)
    parser.add_argument('-v', '--verbose', help="Print extra information about the process",
                        action="store_const", dest="loglevel", const=logging.INFO)
    # turn those words into arguments/variables
    args = parser.parse_args()

    # set up the logging defaults
    logging.basicConfig(level=args.loglevel,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    return vars(args)


if __name__ == "__main__":
    main()
