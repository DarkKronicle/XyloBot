import discord
from discord.ext import commands
from Storage import *


async def getuser(nick: str, guild: discord.Guild) -> discord.Member:
    """
    Gets a user based off of their current displayname (nick)

    :param nick: User's current nick
    :param guild: Guild
    :return: Member
    """
    member: discord.Member
    for member in guild.members:
        if member.display_name == nick:
            return member
    return None


class Commands(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx: commands.Context):
        """
        Check to see if the bot is responsive.
        """

        await ctx.send("Pong!")

    @commands.command(name="whoami")
    async def whoami(self, ctx: commands.Context):
        """
        Grabs data stored in the database about the sender.
        """
        id = ctx.message.author.id
        storage = Storage()
        data = storage.get_user_data(id)

        if data is None:
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
    async def whois(self, ctx: commands.Context, *args):
        """
        Grabs data stored in the database about the specified user.
        """
        if len(args) <= 0:
            embed = discord.Embed(
                title="Not Enough Arguments",
                description="`>whois <user>`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed, delete_after=15)
            return

        user = await getuser(' '.join(args), ctx.guild)

        if user is None:
            embed = discord.Embed(
                title="Not found!",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        storage = Storage()
        data = storage.get_user_data(user.id)

        if data is None:
            embed = discord.Embed(
                title="Not found!",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )
        else:
            embed = discord.Embed(
                title="Who is: `" + str(user.name) + "`",
                description="Name: `" + data[0] + "` School: `" + data[1] + "`",
                colour=discord.Colour.blurple()
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
