import json
import math
import os
import random
from datetime import datetime

import discord
from discord.ext import commands

from util.context import Context


class Counter:

    def __init__(self, *, values=None):
        if values is not None:
            self.last_id = values["last_id"]
            self.count = values["count"]
        else:
            self.last_id = 0
            self.count = 0

    def to_dict(self):
        return {
            "count": self.count,
            "last_id": self.last_id
        }

    def set_count(self, number):
        self.count = number
        return self.count

    def increment(self):
        self.count = self.count + 1
        return self.count

    def decrement(self):
        self.count = self.count - 1
        return self.count

    def is_last(self, user_id):
        if user_id == self.last_id:
            return True
        else:
            self.last_id = user_id
            return False


class Counting(commands.Cog):
    counter_name = "data/counter.json"

    def __init__(self, bot):
        self.bot = bot
        # I want this to be persistent through multiple commands.
        self.counter_cooldown = self.command_cooldown = commands.CooldownMapping.from_cooldown(1, 10, commands.BucketType.user)

        # Load up the global counter
        exists = os.path.exists(self.counter_name)
        with open(file=self.counter_name, mode="a+") as f:
            f.seek(0)
            if exists:
                self.counter = Counter(values=json.load(f))
            else:
                self.counter = Counter()

    def cog_unload(self):
        # Save the counting
        with open(file=self.counter_name, mode='w') as json_file:
            json.dump(self.counter.to_dict(), json_file, indent=4, sort_keys=True)

    @commands.command(name="!setcounter", hidden=True)
    @commands.is_owner()
    async def set_counter(self, ctx: Context, number: int = None):
        """
        Sets the global counter. Owner only.
        """
        if number is None:
            return await ctx.send_help('!setcounter')
        await ctx.send(f"Set to {self.counter.set_count(number)}")

    @commands.command(name="count")
    async def count_cur(self, ctx: Context):
        """
        For the number pacifists, here's the current number.
        """
        embed = discord.Embed(
            description=f"Current number of the global counter is `{self.counter.count}`.",
            colour=discord.Colour.light_gray()
        )
        await ctx.send(embed=embed)

    add_messages = [
        "We're moving up!",
        "Thank you very much :)",
        "How kind of you.",
        "At this rate we'll get to 10^5321 soon.",
        "*ZOOOOMIN*",
        "Sup",
        "<a:deploy:771180662643490817>",
        "<:fblike:771180783217410098>",
        "<:pog:771175687516061726>",
        "Hmm, you bored too?",
        "Up up up up up up up up",
        "You are bringing good to the world.",
        "Convert decrementers with all of your might!",
        "+ FOREVER"
    ]

    @commands.command(name="increment", aliases=["i", "inc", "+"])
    async def increment(self, ctx: Context):
        """
        Play with the global counter!
        """
        # Error handling/cooldown.
        bucket = self.counter_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await ctx.message.delete()
            return await ctx.send(embed=discord.Embed(
                description=f"You're currently on cooldown. Try again in `{math.ceil(retry_after)}` seconds. Right "
                            f"now we're at {self.counter.count}.",
                colour=discord.Colour.red()
            ), delete_after=15)

        # Don't want them to increment it all by themselves.
        if self.counter.is_last(ctx.author.id):
            await ctx.message.delete()
            return await ctx.send(embed=discord.Embed(
                description=f"You were the last one to mess with the counter! Right now we're at {self.counter.count}.",
                colour=discord.Colour.red()
            ), delete_after=15)
        # end

        await ctx.message.delete()
        number = self.counter.increment()
        parrot = "<a:deploy:771180662643490817>"
        embed = discord.Embed(
            colour=discord.Colour.green()
        )
        embed.set_author(name=f"{number} - {ctx.author.display_name}", url=ctx.author.avatar_url)
        embed.set_footer(text=f"To contribute use {ctx.prefix}+ or {ctx.prefix}-")
        if number % 1000 == 0:
            embed.colour = discord.Colour.gold()
            embed.description = f"{parrot} WE GOT TO ***{number}*** {parrot}"
            await ctx.send(embed=embed)
        elif number % 100 == 0:
            embed.description = f"{parrot} TO {number} AND BEYOND {parrot}"
            embed.colour = discord.Colour.magenta()
            await ctx.send(embed=embed)
        else:
            embed.description = random.choice(self.add_messages)
            await ctx.send(embed=embed)

    remove_messages = [
        "Welcome to the dark side.",
        "Yes yes yes",
        "*Evil laughing*",
        "How does it feel to hate on the incrementers?",
        "DOWN WITH THE NUMBER. *ALL HAIL -*",
        "You are making enemies. Good.",
        "*Slow mo walking*"
    ]

    @commands.command(name="decrement", aliases=["d", "dec", "-"])
    async def decrement(self, ctx: Context):
        """
        Play with the global counter!
        """
        # Error handling/cooldown.
        bucket = self.counter_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            await ctx.message.delete()
            return await ctx.send(embed=discord.Embed(
                description=f"You're currently on cooldown. Try again in `{math.ceil(retry_after)}` seconds. Right "
                            f"now we're at {self.counter.count}.",
                colour=discord.Colour.red()
            ), delete_after=15)

        # Don't want them to increment it all by themselves.
        if self.counter.is_last(ctx.author.id):
            await ctx.message.delete()
            return await ctx.send(embed=discord.Embed(
                description=f"You were the last one to mess with the counter! Right now we're at {self.counter.count}.",
                colour=discord.Colour.red()
            ), delete_after=15)
        # end

        await ctx.message.delete()
        number = self.counter.decrement()
        parrot = "<a:deploy:771180662643490817>"
        embed = discord.Embed(
            colour=discord.Colour.red()
        )
        embed.set_author(name=f"{number} - {ctx.author.display_name}", url=ctx.author.avatar_url)
        embed.set_footer(text=f"To contribute use {ctx.prefix}+ or {ctx.prefix}-")
        if number % 1000 == 0:
            embed.colour = discord.Colour.dark_red()
            embed.description = f"{parrot} WE'RE BRINGING IT DOWN TOWN TO ***{number}*** {parrot}"
            await ctx.send(embed=embed)
        elif number % 100 == 0:
            embed.description = f"{parrot} TO {number} AND BELOW {parrot}"
            embed.colour = discord.Colour.dark_red()
            await ctx.send(embed=embed)
        else:
            embed.description = random.choice(self.remove_messages)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Counting(bot))
