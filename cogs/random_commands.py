import random

import discord
import requests
from discord.ext import commands

from storage.json_reader import JSONReader
from util.context import Context


class RandomCommands(commands.Cog, name="Random"):
    """
    Fun commands that may be seeded...
    """

    random_values = JSONReader("data/random.json").data

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
        """
        Rates someone.
        """
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
            message = f"OH WOW. {user.display_name} is ***baaaaad***. You get a fat {str(rating)}/10. L."
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
                      f"round of applause for {user.display_name}! ***10/10!*** "
        else:
            message = f"I have no clue how you did it. You somehow broke me. You should not be here. Here's your {str(rating)}/10. "
        await ctx.send(message)

    @commands.command(name="president", aliases=["pres"])
    async def president(self, ctx: Context, *, user: discord.Member = None):
        """
        Chooses a random president that is 'most' similar to a user.
        """
        if user is None:
            user = ctx.author

        prefix = user.display_name + " is clearly most similar to the President himself, {}!"
        if await ctx.bot.is_owner(user):
            return await ctx.send(prefix.format("George Washington"))

        pres = self.seeded_choose(user.id, self.random_values["presidents"])
        await ctx.send(prefix.format(pres))

    @commands.command(name="number", aliases=["num"])
    async def number(self, ctx, min_num=0, max_num=15):
        """
        Displays a random number between minimum and maximum.
        """
        if max_num > 1500:
            max_num = 1500
        if min_num >= max_num:
            return await ctx.send("Minimum is larger than maximum.")

        await ctx.send(f"Here's your random number: `{random.randint(min_num, max_num)}`")

    @commands.command(name="idea", aliases=["lb", "lightbulb"])
    async def idea(self, ctx: Context):
        """
        Sends you a random idea.
        """
        message = "Something"
        await ctx.send(message)

    @commands.command(name="ship", aliases=["compat"])
    @commands.guild_only()
    async def ship(self, ctx: Context, *, ship1: discord.Member = None):
        if ship1 is None:
            ship1 = ctx.author
        answer = await ctx.ask(f"Who should be shipped with {ship1.display_name}?")
        if answer is None:
            return ctx.timeout()
        guild: discord.Guild = ctx.guild
        ship2 = guild.get_member_named(answer)
        if ship2 is None or ship1 is ship2:
            return await ctx.send("Please put in 2 proper users.")

        ship = self.seeded_int(ship1.id + ship2.id, 0, 50)
        if ship == 0:
            message = "**OH NO. PLEASE NO** {0} and {1} have ***no*** compatibility. {2}/50 :("
        elif ship <= 10:
            message = "{0} and {1} are equivalent to a one night fling. They deeply regret all past relations. {2}/50."
        elif ship <= 20:
            message = "They see each other and grow hopeful of a friendship, but they still pass each other walking. " \
                      "Not looking great {0} and {1}. {2}/50. "
        elif ship <= 30:
            message = "The warm embrace of {0} is something that {1} looks forward to everyday. {2}/50."
        elif ship <= 38:
            message = "Everyday they see each other and smile at the thought of being together. {0} and {1} have a " \
                      "compatibility of {2}/50. "
        elif ship <= 45:
            message = "{0} has finally transcended best friendship with {1}. They have made it to longing for each " \
                      "other. {2}/50. "
        elif ship <= 49:
            message = "How they did it, I don't know. These two are extremely close and love spending time with each " \
                      "other. Good job {0} and {1}. *{2}/50*. "
        elif ship == 50:
            message = "***CONGRATS*** {0} and {1} are *officially* soulmates! Party time baby!! {2}/50"
        else:
            message = "There love for each other broke me. {0} and {1} got a {2}/50."

        await ctx.send(message.format(ship1.display_name, ship2.display_name, str(ship)))

    @commands.command(name="product", aliases=["sell", "tft"])
    async def this_for_that(self, ctx: Context):
        """
        This for that

        http://itsthisforthat.com/api.php?json
        """
        data = requests.get("http://itsthisforthat.com/api.php?json").json()
        message = "So, basically, it's like a {} for {}."
        await ctx.send(message.format(data["this"], data["that"]))

    @commands.command(name="worth", aliases=["price"])
    async def worth(self, ctx: Context, *, user: discord.Member = None):
        """
        How much are you worth?
        """
        if user is None:
            user = ctx.author

        if user.id == ctx.bot.user.id:
            return await ctx.send("I am clearly worth approximately $10*5^29^31.")

        if await ctx.bot.is_owner(user):
            return await ctx.send("For my humble master, his worth is unmeasurable.")

        def worth_conversion(x):
            return (x ^ 4) / (10 ^ 15)

        price = worth_conversion(self.seeded_int(user.id, 0, 100001))

        message = "{0} is clearly worth ${1}."
        await ctx.send(message.format(user.display_name, price))


def setup(bot):
    bot.add_cog(RandomCommands())
