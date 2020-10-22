from discord.ext import commands
import discord
from util import context
from util import streaming
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

    @check_request
    def raw_lines(self):
        return self.get_data_cat("total")["lines"]

    def format(self, d):
        language = d["language"]
        files = d["files"]
        lines = d["lines"]
        code = d["linesOfCode"]


class API(commands.Cog):

    @commands.group(name="twitch", usage="<info>", invoke_without_command=True)
    async def twitch(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('twitch')

    # @twitch.command(name="info", usage="<channelname>")
    async def twitch_info(self, ctx: context.Context, *args):
        if len(args) == 0:
            await ctx.send_help('twitch info')
            return

        channel = args[0]
        data = await streaming.check_twitch_online(channel)
        if data is None:
            return await ctx.send(f"{channel} is currently not streaming!")

        embed = discord.Embed(
            title=f"{data['title']} - {channel}",
            description=f"{channel} is currently streaming!\n\nhttps://twitch.tv/{channel}",
            colour=discord.Colour.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="cloc")
    async def cloc(self, ctx: Context, *args):
        if len(args) == 0:
            return await ctx.send("You need to specify a github repo. `<user>/<project>`.")

    @commands.command(name="lmgtfy", aliases=["lemmegoogle"])
    async def lmgtfy(self, ctx: Context, *args):
        """
        Send a passive agressive google it review.
        """
        if len(args) == 0:
            return await ctx.send_help('lmgtfy')
        content = ' '.join(args)
        url = f"<https://lmgtfy.app/?q={content}&iie=1>"
        url = url.replace(' ', '+')
        await ctx.send(f"I have the perfect solution for you! Click here:\n{url}")

    @commands.command(name="google")
    async def google(self, ctx: Context, *args):
        """
        Sends a google search link
        """
        if len(args) == 0:
            return await ctx.send_help('google')
        content = ' '.join(args)
        url = f"<https://google.com/search?q={content}>"
        url = url.replace(' ', '%20')
        await ctx.send(f"I have the perfect solution for you! Click here:\n{url}")

    @commands.command(name="imagegoogle", aliases=["igoogle"])
    async def igoogle(self, ctx: Context, *args):
        """
        Sends a google search link
        """
        if len(args) == 0:
            return await ctx.send_help('imagegoogle')
        content = ' '.join(args)
        url = f"<https://www.google.com/search?tbm=isch&q={content}>"
        url = url.replace(' ', '%20')
        await ctx.send(f"I have the perfect image for you! Click here:\n{url}")

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name="yoda", aliases=["yodaspeak"])
    async def yoda(self, ctx: Context, *args):
        """
        Translates text into Yoda
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
