import discord
from discord.ext import commands
from cogs.games.fire_draw import FireDrawGame
from util.context import Context

guild_games = []


class Game:
    users = []

    def __init__(self, channel, owner):
        self.channel: discord.TextChannel = channel
        self.owner: discord.User = owner
        guild_games.append(channel.guild)

    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)

    async def start(self, bot):
        pass

    async def timeout(self):
        pass

    async def end(self, user):
        pass


class Games(commands.Cog):

    @commands.group(name="play", usage="<game>", invoke_without_command=True)
    async def play(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help('play')

    @play.command(name="duel", usage="<user>")
    async def fire_draw(self, ctx: Context, user: discord.Member = None):
        if user is None:
            await ctx.send("Specify a correct user!")

        guild_games.append(ctx.guild)
        answer = await ctx.prompt(f"{ctx.author.mention} has challenged {user.mention} to a duel! Do you accept? Respond with "
                         f"`yes` or `no`", delete_after=False)
        if answer is None or not answer:
            await ctx.send("Just when it was about to get spicy, everyone left.")

        duel = FireDrawGame(ctx.channel, ctx.author)

        duel.add_user(user)
        await duel.start(ctx.bot)

def setup(bot):
    bot.add_cog(Games())