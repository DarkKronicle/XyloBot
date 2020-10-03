import discord
from discord.ext import commands
from cogs.games.fire_draw import FireDrawGame
from util.context import Context


class Games(commands.Cog):
    current_games = {}

    @commands.group(name="play", usage="<game>", invoke_without_command=True)
    async def play(self, ctx: Context):
        """
        Play a game.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('play')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild in self.current_games:
            game = self.current_games[message.guild]
            if message.author in game.users and message.channel is game.channel:
                await message.delete()

    @play.command(name="duel", usage="<user>")
    async def fire_draw(self, ctx: Context, user: discord.Member = None):
        """
        First person to type out a random set of characters.
        """
        if user is None or user is ctx.author:
            await ctx.send("Specify a correct user!")

        answer = await ctx.prompt(
            f"{ctx.author.mention} has challenged {user.mention} to a duel! Do you accept? Respond with "
            f"`yes` or `no`", author_id=user.id, delete_after=False)
        if answer is None or answer == False:
            await ctx.send("Just when it was about to get spicy, everyone left.")
            return

        duel = FireDrawGame(ctx.channel, ctx.author)
        self.current_games[ctx.guild] = duel
        duel.add_user(user)
        await duel.start(ctx.bot)
        self.current_games.pop(ctx.guild)


def setup(bot):
    bot.add_cog(Games())
