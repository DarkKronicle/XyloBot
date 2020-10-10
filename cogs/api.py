from discord.ext import commands
import discord
from util import context
from util import streaming
from util.context import Context


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

    @commands.command(name="lmgtfy", aliases=["lemmegoogle"])
    async def lmgtfy(self, ctx: Context, *args):
        """
        Send a passive agressive google it review.
        """
        if len(args) == 0:
            return ctx.send_help('lmgtfy')
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
            return ctx.send_help('google')
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
            return ctx.send_help('imagegoogle')
        content = ' '.join(args)
        url = f"<https://www.google.com/search?tbm=isch&q={content}>"
        url = url.replace(' ', '%20')
        await ctx.send(f"I have the perfect image for you! Click here:\n{url}")


def setup(bot):
    bot.add_cog(API())
