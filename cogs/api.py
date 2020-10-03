from discord.ext import commands
import discord
from util import context
from util import streaming


class API(commands.Cog):

    @commands.group(name="twitch", usage="<info>", invoke_without_command=True)
    async def twitch(self, ctx: context.Context):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help('twitch')

    @twitch.command(name="info", usage="<channelname>")
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

def setup(bot)
    bot.add_cog(API())