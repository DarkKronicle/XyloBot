import random

import discord
from discord.ext import commands

from storage.json_reader import JSONReader
from util.context import Context


class RandomCommands(commands.Cog, name="Random"):

    random_values = JSONReader.loadfile("data/random.json").data

    def seeded_int(self, obj_id, min_int=0, max_int=1):
        random.seed(obj_id)
        value = random.randint(min_int, max_int)
        random.seed()
        return value

    def seeded_choose(self, obj_id, objects):
        random.seed(obj_id)
        value = random.choice(objects)
        random.seed()
        return value

    @commands.command(name="rate")
    async def rate(self, ctx: Context, *, user: discord.Member = None):
        if user is None:
            user = ctx.author

        if user.id == ctx.bot.user.id:
            message = "Oh... you're asking me? Well I'll say I'm a solid 10/10 :)"
            return await ctx.send(message)

        if await ctx.bot.is_owner(user):
            message = "Now this may be boring, but I'm legally obliged to say that this person is a 1000/10. Please " \
                      "give it up to my creator! *Wooooo* "
            return await ctx.send(message)

        rating = self.seeded_int(user.id, 0, 10)

        if rating == 0:
            message = f"OH WOW. {user.display_name} is ***baaaaad***. You get a fat {str(rating)}/10"
        elif rating <= 3:
            message = f"I'm not super impressed by {user.display_name}... I guess I'll give them a {str(rating)}/10."
        elif rating <= 6:
            message = f"Meh, thats pretty ok. {user.display_name} got a pretty average {str(rating)}/10."
        elif rating <= 7:
            message = f"Hey, that's pretty good. {user.display_name} is totally a {str(rating)}/10."
        elif rating <= 9:
            message = f"Wow. *Slow Clap* You are easily one of the best people I know. {user.display_name} gets a " \
                      f"whopping **{str(rating)}/10!** "
        elif rating == 10:
            message = f"OH MAN. ***OOOOO BABY!*** We are among a *legend*. Ladies and gentlmen, please give a big " \
                      f"round of applause for {user.display_name}! ***10/10*** "
        else:
            message = f"I have no clue how you did it. You somehow broke me. You should not be here. Here's your {str(rating)}/10. "
        await ctx.send(message)

    @commands.command(name="president", aliases=["pres"])
    async def president(self, ctx: Context, *, user: discord.Member = None):
        if user is None:
            user = ctx.author

        prefix = ctx.author.display_name + " is clearly most similar to the President himself, {}!"
        if await ctx.bot.is_owner(user):
            return await ctx.send(prefix.format("George Washington"))

        pres = self.seeded_choose(user.id, self.random_values["presidents"])
        await ctx.send(prefix.format(pres))

def setup(bot):
    bot.add_cog(RandomCommands())
