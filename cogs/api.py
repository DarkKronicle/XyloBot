import random

from discord.ext import commands
import discord
from util import context
from util.context import Context
import requests
from functools import wraps


def check_request(func):
    # Checks to make sure that the request was actually successful before doing anything.
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.data is None:
            return None
        elif not self.data:
            return False

        return func(self, *args, **kwargs)

    return wrapper


class LineCount:
    """
    https://codetabs.com/count-loc/count-loc-online.html

    A class that gets the amount of lines from a GitHub repo and can format it.
    """

    def __init__(self, user, repo):
        self.user = user
        self.repo = repo
        self.data = self.get_lines()

    def get_lines(self):
        """
        Gets the lines of code from a github repository. Returns a dict if everything went well, False if there was an error,
        None if there was no data.
        """
        url = f"https://api.codetabs.com/v1/loc/?github={self.user}/{self.repo}"
        r = requests.get(url)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            # Probably a 429 (Too many requests)
            return False
        data = r.json()
        if "error" in data:
            # Something didn't work well with this.
            return None

        return data

    def get_data_cat(self, category):
        category = category.lower()
        for d in self.data:
            if "language" in d and d["language"].lower() == category:
                return d
        return None

    def get_total(self):
        total = self.get_data_cat("total")
        return total

    @check_request
    def raw_lines(self):
        return self.get_data_cat("total")["lines"]

    @check_request
    def format_random(self):
        cat: dict = random.choice(self.data)
        cat = cat.copy()
        language = cat["language"]
        if language == "Total":
            language = "total"

        # Remove 0's and language stats.
        for f, v in cat.copy().items():
            if v == 0:
                cat.pop(f)
            if f == "language":
                cat.pop(f)
        fields = list(cat)

        # This is what will be formatted.
        field = random.choice(fields)
        value = cat[field]

        # 0 is language, 1 is the data
        names = {
            "files": "{1} {0} files",
            "lines": "{1} lines in {0}",
            "blanks": "{1} blanks in {0}",
            "comments": "{1} comments in {0}",
            "linesOfCode": "{1} lines of code in {0}"
        }
        if field in names:
            message = names[field].format(str(language), str(value))
        else:
            # If all goes wrong, just give it to them raw
            message = "{1} {2} in {0}"
            message = message.format(str(language), str(value), str(field))

        return message

    def format(self, d):
        language = d["language"]
        files = d["files"]
        lines = d["lines"]
        code = d["linesOfCode"]
        comments = d["comments"]
        blanks = d["blanks"]
        message = f"**{language}:**\nFiles: `{files}`. Lines: `{lines}`. Lines of code: `{code}`. Comments: " \
                  f"`{comments}`. Blanks: `{blanks}`. "
        return message

    def format_all(self):
        message = ""
        for d in self.data:
            message = message + self.format(d) + "\n"
        return message


class API(commands.Cog):
    """
    Use different API commands.
    """

    @commands.command(name="cloc", usage="<user>/<project>", aliases=["lines"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cloc(self, ctx: Context, *args):
        """
        View line count of a GitHub repository.
        """
        if len(args) == 0:
            return await ctx.send("You need to specify a github repo. `<user>/<project>`.")

        split = args[0].split("/")
        if len(split) != 2:
            return await ctx.send("Make sure you specify the user and the project! `<user>/<project>`.")
        async with ctx.typing():
            data = LineCount(split[0], split[1])
            if data.data is None:
                return await ctx.send("No repository found with that name.")
            if not data.data:
                return await ctx.send("Too many requests in the past 5 seconds. Try again later.")
            embed = discord.Embed(
                title=f"Line count for {args[0]}",
                description=data.format_all(),
                colour=discord.Colour.green()
                                  )
            embed.url = f"https://github.com/{split[0]}/{split[1]}/"
            await ctx.send(embed=embed)

    @commands.command(name="lmgtfy", aliases=["lemmegoogle"])
    async def lmgtfy(self, ctx: Context, *args):
        """
        Send a passive aggressive google it review.
        """
        if len(args) == 0:
            return await ctx.send_help('lmgtfy')
        content = ' '.join(args)
        url = f"<https://lmgtfy.app/?q={content}&iie=1>"
        url = url.replace(' ', '+')
        await ctx.send(embed=discord.Embed(
            description=f"I have the perfect solution for you! [Click here]({url})\n\n`{content}`",
            colour=discord.Colour.blue()
        ))

    @commands.command(name="google")
    async def google(self, ctx: Context, *args):
        """
        Sends a google search link.
        """
        if len(args) == 0:
            return await ctx.send_help('google')
        content = ' '.join(args)
        url = f"<https://google.com/search?q={content}>"
        url = url.replace(' ', '%20')
        await ctx.send(embed=discord.Embed(
            description=f"I have the perfect solution for you! [Click here]({url})\n`{content}`",
            colour=discord.Colour.blue()
        ))

    @commands.command(name="imagegoogle", aliases=["igoogle"])
    async def igoogle(self, ctx: Context, *args):
        """
        Sends a google image search link
        """
        if len(args) == 0:
            return await ctx.send_help('imagegoogle')
        content = ' '.join(args)
        url = f"<https://www.google.com/search?tbm=isch&q={content}>"
        url = url.replace(' ', '%20')
        await ctx.send(embed=discord.Embed(
            description=f"I have the perfect solution for you! [Click here]({url})\n`{content}`",
            colour=discord.Colour.blue()
        ))

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name="yoda", aliases=["yodaspeak"])
    async def yoda(self, ctx: Context, *args):
        """
        Translates text into Yoda.
        """
        if len(args) == 0:
            return await ctx.send_help('yoda')
        content = ' '.join(args)
        url = f"https://api.funtranslations.com/translate/yoda.json?text={content}"
        url = url.replace(' ', '%20')
        data = requests.get(url=url).json()
        if "error" in data:
            return await ctx.send("Looks like this has been used too much!")
        await ctx.send(data["contents"]["translated"])


def setup(bot):
    bot.add_cog(API())
