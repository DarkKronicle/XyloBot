import discord
from discord.ext import commands, tasks
import dbl

from xylo_bot import XyloBot


class BotList(commands.Cog):
    """
    Allows me to update info for Bot Lists.
    """

    def __init__(self, bot):
        self.bot: XyloBot = bot
        self.token = self.bot.config['dbl_token']
        self.dblpy = dbl.DBLClient(self.bot, self.token)
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.stop()

    @tasks.loop(minutes=30)
    async def update_stats(self):
        """This function runs every 30 minutes to automatically update your server count."""
        await self.bot.wait_until_ready()
        try:
            server_count = len(self.bot.guilds)
            await self.dblpy.post_guild_count(server_count)
        except Exception as e:
            await self.bot.log.send(discord.Embed(
                title="Failed to update server count",
                description='Failed to post server count\n{}: {}'.format(type(e).__name__, e),
                colour=discord.Colour.red()
            ))

    @commands.Cog.listener()
    async def on_dbl_upvote(self, data):
        await self.bot.log.send(discord.Embed(
            title="New Vote!",
            description=data,
            colour=discord.Colour.gold()
        ))


def setup(bot):
    bot.add_cog(BotList(bot))
