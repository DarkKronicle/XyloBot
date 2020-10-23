import asyncio
import json
from json import JSONDecodeError

import discord
from discord.ext import commands

from cogs.games import quiz
from cogs.games.fire_draw import FireDrawGame
from cogs.games.cah import CAHGameInstance
from storage.json_reader import JSONReader
from util import discord_util
from util.context import Context


class Games(commands.Cog):
    """
    Games that users can play.
    """
    current_games = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel in self.current_games:
            if len(self.current_games[message.channel]) != 0:
                for g in self.current_games[message.channel]:
                    game = self.current_games[message.channel][g]
                    if message.channel is game.channel:
                        if message.author in game.users:
                            await game.process_message(message)

    @commands.command(name="duel", usage="<user>", aliases=["gun", "wordduel"])
    @commands.guild_only()
    async def fire_draw(self, ctx: Context, user: discord.Member = None):
        """
        First person to type out a random set of characters.
        """
        if ctx.channel in self.current_games and "duel" in self.current_games[ctx.channel]:
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
        if ctx.channel not in self.current_games:
            self.current_games[ctx.channel] = {}
        self.current_games[ctx.channel]["duel"] = duel
        duel.add_user(user)
        await duel.start(ctx.bot)
        self.current_games[ctx.channel].pop("duel")

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
    async def cah_start(self, ctx: Context, *args):
        """
        Start a game of Cards Against Humanity. You can send it again to force it to start.
        """
        if ctx.channel in self.current_games and "cah" in self.current_games[ctx.channel]:
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
            description=f"The game is being setup, get people to join using `{ctx.prefix}cah join`. "
                        f"When everyone is you can `{ctx.prefix}cah start` again to force start. The "
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
        if ctx.channel not in self.current_games:
            self.current_games[ctx.channel] = {}
        game = CAHGameInstance(ctx.channel, ctx.author, self.cah_done, categories, ctx.bot)
        self.current_games[ctx.channel]["cah"] = game
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

    async def cah_done(self, channel):
        self.current_games[channel].pop("cah")

    @cah.command(name="join")
    @commands.guild_only()
    async def cah_join(self, ctx):
        if ctx.channel not in self.current_games or "cah" not in self.current_games[ctx.channel]:
            return await ctx.send("No games currently going on. Start one with `cah start`")
        game = self.current_games[ctx.channel]["cah"]
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

    async def quiz_force(self, game, ctx):
        message = f"Game starting for *Quiz*."
        start = discord.Embed(
            title="Quiz - Game starting!",
            description=message,
            colour=discord.Colour.blue()
        )
        game.started = True
        await ctx.send(embed=start)
        await asyncio.sleep(2)
        await game.start(ctx.bot)

    @quiz.command(name="start", usage="<max_points>")
    async def quiz_start(self, ctx: Context, *args):
        if ctx.channel in self.current_games and "quiz" in self.current_games[ctx.channel]:
            game = self.current_games[ctx.channel]["quiz"]
            if game.started:
                wait = discord.Embed(
                    title="Game already going on!",
                    description="There is already a *Quiz* game going on in your server. Please wait.",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=wait)
            else:
                if ctx.author is game.owner:
                    await self.quiz_force(game, ctx)
            return

        message: discord.Message = ctx.message
        if len(message.attachments) != 1:
            return await ctx.send("Send a JSON file with the start to get a quiz!")

        attachment: discord.Attachment = message.attachments[0]
        name: str = attachment.filename
        if not name.endswith(".json"):
            return await ctx.send("Please send a proper JSON file. Build one with `>json 'QUESTION|ANSWER' 'QUESTION|ANSWER'...`")

        buffer = await discord_util.get_data_from_url(attachment.url)
        if buffer is None:
            await ctx.send("Something went wrong getting your file. Make sure your file is correct.")
            return

        # json_raw = buffer.read().decode('UTF-8')
        try:
            questions = json.load(buffer)
        except JSONDecodeError:
            return await ctx.send("Error while reading your file.")

        for key in questions:
            if not isinstance(key, str) or not isinstance(questions[key], str):
                return await ctx.send("All keys and values need to be strings!")

        await ctx.message.delete()

        if len(args) > 0:
            try:
                max_num = int(args[0])
            except ValueError:
                max_num = 5
        else:
            max_num = 5

        game = quiz.QuizGameInstance(ctx.channel, ctx.author, self.quiz_done, questions=questions, max_score=max_num)
        if ctx.channel not in self.current_games:
            self.current_games[ctx.channel] = {}
        self.current_games[ctx.channel]["quiz"] = game
        await ctx.send(f"Game started! Get people to join with `{ctx.prefix}quiz join`.")
        await asyncio.sleep(60)
        if not game.started:
            await game.start(ctx.bot)

    @quiz.command(name="join")
    @commands.guild_only()
    async def quiz_join(self, ctx):
        if ctx.channel not in self.current_games or "quiz" not in self.current_games[ctx.channel]:
            return await ctx.send("No games currently going on. Start one with `cah quiz`")
        game = self.current_games[ctx.channel]["quiz"]
        if ctx.author in game.users:
            await ctx.send("You're already in a game!")
            return
        await game.add_user(ctx.author)
        add = discord.Embed(
            title="User added to Quiz!",
            description=f"{ctx.author.mention} has been added to the current game of *Quiz*!",
            colour=discord.Colour.dark_green()
        )
        add.set_footer(text=f"There are now currently {len(game.users)} users.")
        await ctx.send(embed=add)

    async def quiz_done(self, channel):
        self.current_games[channel].pop("quiz")


def setup(bot):
    bot.add_cog(Games())
