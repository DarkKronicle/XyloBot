from discord.ext import commands


class ClipList(commands.Cog):
    """
    A clips extension for storing lists.
    """

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(ClipList(bot))
