# import json
import argparse
import logging
import os
from discord.ext import tasks
import traceback

import discord
from discord.ext.commands import Bot
import random

BOT_PREFIX = ">"
bot = Bot(command_prefix=BOT_PREFIX)
# We create our own in cogs/Help.py
bot.remove_command('help')
# Command Extensions
startup_extensions = ["Commands", "Setup", "Help"]
# Extension directory
cogs_dir = "cogs"


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    status.start()


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
        act = discord.Activity(name="to Marimba.", type=discord.ActivityType.listening)
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
