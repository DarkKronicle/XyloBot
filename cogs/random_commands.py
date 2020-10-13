from random import random

import discord
from discord.ext import commands

from util.context import Context


class RandomCommands(commands.Cog, name="Random"):

    def seeded_int(self, obj_id, min_int=0, max_int=1):
        random.seed(obj_id)
        value = random.randint(min_int, max_int)
        random.seed()
        return value

    @commands.command(name="rate")
    async def rate(self, ctx: Context, *, user: discord.Member = None):
        if user is None:
            return await ctx.send("Specify a correct user!")

        rating = self.seeded_int(user.id, 0, 10)

        if rating == 0:
            message = f"OH WOW. {user.display_name} is ***baaaaad***. You get a fat {str(rating)}/10"
        elif rating <= 3:
            message = f"I'm not super impressed by {user.display_name}... I guess I'll give them a {str(rating)}/10."
        elif rating <= 7:
            message = f"Eyy, that's pretty good. {user.display_name} is totally a {str(rating)}/10."
        elif rating <= 9:
            message = f"Wow. *Slow Clap* You are easily one of the best people I know. {user.display_name} gets a " \
                      f"whopping **{str(rating)}/10!** "
        elif rating == 10:
            message = f"OH MAN. ***OOOOO BABY!*** We are among a *legend*. Ladies and gentlmen, please give a big " \
                      f"round of applause for {user.display_name}! ***10/10*** "
        else:
            message = f"I have no clue how you did it. You somehow broke me. You should not be here. Here's your {str(rating)}/10. "
        await ctx.send(message)

def setup(bot):
    bot.add_cog(RandomCommands())
