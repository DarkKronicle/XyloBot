import asyncio

import discord
from discord.ext import commands

from cogs.games import quiz
from cogs.games.fire_draw import FireDrawGame
from cogs.games.cah import CAHUserInstance, CAHGameInstance
from storage.json_reader import JSONReader
from util.context import Context
from storage import cache


def is_game_channel():
    async def predicate(context: commands.Context):
        channel = cache.get_game_channel(context.guild)
        if channel is not None:
            return context.channel is channel
        return False

    return commands.check(predicate)


class Games(commands.Cog):
    """
    Games that users can play.
    """
    current_games = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild in self.current_games:
            if len(self.current_games[message.guild]) != 0:
                for g in self.current_games[message.guild]:
                    game = self.current_games[message.guild][g]
                    if message.channel is game.channel:
                        if message.author in game.users:
                            await game.process_message(message)

    @commands.command(name="duel", usage="<user>", aliases=["gun", "wordduel"])
    @commands.guild_only()
    @is_game_channel()
    async def fire_draw(self, ctx: Context, user: discord.Member = None):
        """
        First person to type out a random set of characters.
        """
        if ctx.guild in self.current_games and "duel" in self.current_games[ctx.guild]:
            await ctx.send("There's already a duel going on. Please wait")
            return
        if user is None or user is ctx.author:
            await ctx.send("Specify a correct user!")

        answer = await ctx.prompt(
            f"{ctx.author.mention} has challenged {user.mention} to a duel! Do you accept? Respond with "
            f"`yes` or `no`", author_id=user.id, delete_after=False)
        if answer is None or answer == False:
            await ctx.send("Just when it was about to get spicy, everyone left.")
            return

        duel = FireDrawGame(ctx.channel, ctx.author)
        if ctx.guild not in self.current_games:
            self.current_games[ctx.guild] = {}
        self.current_games[ctx.guild]["duel"] = duel
        duel.add_user(user)
        await duel.start(ctx.bot)
        self.current_games[ctx.guild].pop("duel")

    @commands.group(name="cah", usage="<start|join>")
    async def cah(self, ctx: Context):
        """
        Cards Against Humanity
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('cah')

    cards = JSONReader("data/cah.json").data

    @cah.command(name="start", usage="<all/categories>")
    @commands.guild_only()
    @is_game_channel()
    async def cah_start(self, ctx, *args):
        """
        Start a game of Cards Against Humanity. You can send it again to force it to start.
        """
        if ctx.guild in self.current_games and "cah" in self.current_games[ctx.guild]:
            game = self.current_games[ctx.guild]["cah"]
            if game.started:
                wait = discord.Embed(
                    title="Game already going on!",
                    description="There is already a *Cards Against Humanity* game going on in your server. Please wait.",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=wait)
            else:
                if ctx.author is game.owner:
                    await self.cah_force(game, ctx)
            return
        started = discord.Embed(
            title="Cards Against Humanity - Setting up...",
            description=f"The game is being setup, get people to join using `{cache.get_prefix(ctx.guild)}cah join`. "
                        f"When everyone is you can `{cache.get_prefix(ctx.guild)}cah start` again to force start. The "
                        f"game will start in **one minute**.",
            colour=discord.Colour.green()
        )
        await ctx.send(embed=started)
        if len(args) == 0 or args[0] == "all":
            categories = []
            for cat in self.cards:
                categories.append(cat)
        else:
            categories = []
            for arg in args:
                if arg in self.cards:
                    categories.append(arg)
        if len(categories) == 0:
            categories = ["base"]
        if ctx.guild not in self.current_games:
            self.current_games[ctx.guild] = {}
        game = CAHGameInstance(ctx.channel, ctx.author, self.cah_done, categories, ctx.bot)
        self.current_games[ctx.guild]["cah"] = game
        await asyncio.sleep(60)
        if not game.started:
            await self.cah_force(game, ctx)

    async def cah_force(self, game, ctx):
        if len(game.users) < 3:
            await ctx.send(embed=discord.Embed(
                title="Cards Against Humanity - Not enough people!",
                description=f"Only {len(game.users)} are in the game. You'll need at least 3.",
                colour=discord.Colour.red()
            ))
            return
        message = f"Game starting for *Cards Against Humanity*. Make sure to type your answers in **this channel**.\n\nCategories:"
        for cat in game.categories:
            message = message + f" `{cat}`"
        start = discord.Embed(
            title="Cards Against Humanity - Game starting!",
            description=message,
            colour=discord.Colour.blue()
        )
        game.started = True
        await ctx.send(embed=start)
        await asyncio.sleep(2)
        await game.start(ctx.bot)

    async def cah_done(self, guild):
        self.current_games[guild].pop("cah")

    @cah.command(name="join")
    @commands.guild_only()
    @is_game_channel()
    async def cah_join(self, ctx):
        if ctx.guild not in self.current_games or "cah" not in self.current_games[ctx.guild]:
            return await ctx.send("No games currently going on. Start one with `cah start`")
        game = self.current_games[ctx.guild]["cah"]
        if ctx.author in game.users:
            await ctx.send("You're already in a game!")
            return
        await game.add_user(ctx.author)
        add = discord.Embed(
            title="User added to Cards Against Humanity!",
            description=f"{ctx.author.mention} has been added to the current game of *Cards Against "
                        f"Humanity*!",
            colour=discord.Colour.dark_green()
        )
        add.set_footer(text=f"There are now currently {len(game.users)} users.")
        await ctx.send(embed=add)

    @commands.group(name="quiz", invoke_without_command=True)
    async def quiz(self, ctx: Context):
        await ctx.send_help('quiz')

    @quiz.command(name="start")
    async def quiz_start(self, ctx: Context, *args):
        game = quiz.QuizGameInstance(ctx.channel, ctx.author)
        await game.start(ctx.bot)


def setup(bot):
    bot.add_cog(Games())
