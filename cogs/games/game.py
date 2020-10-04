import asyncio

import discord
from discord.ext import commands
from cogs.games.fire_draw import FireDrawGame
from cogs.games.cah import *
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
    current_games = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild in self.current_games:
            if "cah" in self.current_games[message.guild]:
                game = self.current_games[message.guild]["cah"]
                if message.channel is game.channel:
                    if message.author in game.users:
                        await game.process_message(message)

    @commands.command(name="duel", usage="<user>")
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
            self.current_games[ctx.guild] = []
        self.current_games[ctx.guild]["duel"] = duel
        duel.add_user(user)
        await duel.start(ctx.bot)
        self.current_games[ctx.guild].pop("duel")

    @commands.group(name="cah", usage="<start|join>")
    async def cah(self, ctx):
        pass

    @cah.command(name="start")
    @is_game_channel()
    async def cah_start(self, ctx):
        if ctx.guild in self.current_games and "cah" in self.current_games[ctx.guild]:
            await ctx.send("There's already a cah going on. Please wait")
            return
        await ctx.send("Get people to join using `cah join`. If there's enough people in one minute, I'll start it!")
        if ctx.guild not in self.current_games:
            self.current_games[ctx.guild] = {}
        game = CAHGameInstance(ctx.channel, ctx.author, self.cah_done, ["default"], ctx.bot)
        self.current_games[ctx.guild]["cah"] = game
        await asyncio.sleep(60)
        if len(game.users) < 2:
            await ctx.send("Not enough people!")
            return
        await ctx.send("Lets start!")
        await game.start(ctx.bot)

    async def cah_done(self, guild):
        self.current_games[guild].pop("cah")

    @cah.command(name="join")
    @is_game_channel()
    async def cah_join(self, ctx):
        if ctx.guild not in self.current_games or "cah" not in self.current_games[ctx.guild]:
            return await ctx.send("No games currently going on. Start one with `cah start`")
        game = self.current_games[ctx.guild]["cah"]
        await game.add_user(ctx.author)
        await ctx.send("You've been added to the game!")


def setup(bot):
    bot.add_cog(Games())
