from discord.ext import commands
import discord
from storage.database import *


class Startup(commands.Cog):
    """
    Setup wizards for when easy Xylo use.
    """

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        db = Database()
        if not db.guild_exists(str(guild.id)):
            db.new_guild(str(guild.id), ">")
        for user in guild.members:
            if not user.bot:
                db.add_new_user(str(user.id))

        if guild.owner.dm_channel is None:
            await guild.owner.create_dm()
        dm: discord.DMChannel = guild.owner.dm_channel
        await dm.send(f"Thanks for adding me to {guild.name}! I've started by setting your server's default prefix to "
                      f"`>`. Here's the bare minimum you need to know:\n\n`>help` - The help command. It shows *all* "
                      f"commands that you can use, and the usage on how to use it. You can also get more specific "
                      f"help per command.\n\n`>settings` - This is how you configure what the prefix is, what fun "
                      f"modules are active, utility commands, and more!\n\n`>verification` - Get verification on your "
                      f"server setup! You will then use the `>auth` command to verify users.\n\n`>marks` - Probably "
                      f"my best feature.\n\n\nFinally, if you have any questions or requests, come check out my "
                      f"repository! https://github.com/DarkKronicle/XyloBot/")


def setup(bot):
    bot.add_cog(Startup())
