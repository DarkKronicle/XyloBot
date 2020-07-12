import discord
from discord.ext import commands
from Storage import *

class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send("Pong!")

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     try:
    #         await ctx.message.delete()
    #     finally:
    #         print("An error occurred in " + ctx.message.content)
    #     embed = discord.Embed(
    #         title="Error in command - " + str(type(error)),
    #         description="There was an error in your command, please double check that it was formatted correctly and "
    #                     "if it persists, contact the developer.",
    #         colour=discord.Colour.red()
    #     )
    #     args = ''
    #     embed.add_field(name="Command Used:", value=ctx.message.content)
    #     embed.set_footer(text="Default error message. Deletes after 30 seconds.")
    #     await ctx.send(embed=embed, delete_after=30)

    @commands.command(name="whoami")
    async def whoami(self, ctx):
        id = ctx.message.author.id
        storage = Storage()
        data = storage.getuserdata(id)
        if (data is None):
            embed = discord.Embed(
                title="Not found...",
                description="Talk to a dev if you believe this is an error.",
                colour=discord.Colour.red()
            )
        else:
            embed = discord.Embed(
                title="Who is: `" + str(ctx.message.author.name) + "`",
                description="Name: `" + data[0] + "` School: `" + data[1] + "`",
                colour=discord.Colour.blurple()
            )
        await ctx.send(embed=embed)

    @commands.command(name="whois")
    async def whois(self, ctx, *args):
        if len(args) <= 0:
            embed = discord.Embed(
                title="Not Enough Arguments",
                description="`>whois <user>`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed = embed, delete_after=15)
            return
        user = await self.getuser(' '.join(args), ctx.guild)
        if (user is None):
            embed = discord.Embed(
                title="Not found...",
                description="Talk to a dev if you believe this is an error.",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return
        storage = Storage()
        data = storage.getuserdata(user.id)

        if data is None:
            embed = discord.Embed(
                title="Not found...",
                description="Talk to a dev if you believe this is an error.",
                colour=discord.Colour.red()
            )
        else:
            embed = discord.Embed(
                title="Who is: `" + str(user.name) + "`",
                description="Name: `" + data[0] + "` School: `" + data[1] + "`",
                colour=discord.Colour.blurple()
            )
        await ctx.send(embed=embed)

    async def getuser(self, nick, guild):
        for member in guild.members:
            if (member.display_name == nick):
                return member
        return None

def setup(bot):
    bot.add_cog(Commands(bot))
