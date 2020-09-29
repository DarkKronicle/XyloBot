import discord
from discord.ext import commands
from storage.DatabaseHelper import *
from util.DiscordUtil import *
from storage.Database import *
from discord.ext.commands import has_permissions
import json
from storage import Cache


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

    #@commands.command(name="whoami")
    #@commands.cooldown(1, 30, commands.BucketType.user)
    async def whoami(self, ctx: commands.Context):
        """
        Grabs data stored in the database about the sender.
        """

        if not Cache.get_enabled(ctx.guild):
            return

        id = ctx.message.author.id
        db = Database()
        data = db.get_user(str(ctx.guild.id), str(id))

        if data is None:
            embed = discord.Embed(
                title="Not found...",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )

        else:
            message = f"`{ctx.author.name}`:"
            for f in data["fields"]:
                message = message + f"\n-   {f}: {data['fields'][f]}"

            await ctx.send(message)
            return

        await ctx.send(embed=embed)

    #@commands.command(name="whois")
    async def whois(self, ctx: commands.Context, *args):
        """
        Grabs data stored in the database about the specified user.
        """
        if not Cache.get_enabled(ctx.guild):
            return

        if len(args) <= 0:
            embed = discord.Embed(
                title="Not Enough Arguments",
                description="`>whois <user>`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed, delete_after=15)
            return

        user = ctx.guild.get_member_named(' '.join(args)) 

        if user is None:
            embed = discord.Embed(
                title="Not found!",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        db = Database()
        data = db.get_user(str(ctx.guild.id), str(user.id))

        if data is None:
            embed = discord.Embed(
                title="Not found!",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )
        else:
            message = f"`{user.name}`:`"
            for f in data["fields"]:
                message = message + f"\n-   {f}: `{data['fields'][f]}`"
            await ctx.send(message)
            return

        await ctx.send(embed=embed)

    @commands.command(name="db")
    async def database(self, ctx: commands.Context, *args):
        if await self.bot.is_owner(ctx.author):
            db = Database()
            if len(args) == 0:
                await ctx.send("Nope")
                return

            if args[0] == "create":
                await ctx.send("Creating tables...")
                db.create_tables()
                await ctx.send("Done!")
                return

            if args[0] == "ge" and len(args) > 1:
                await ctx.send("Checking...")
                result = db.guild_exists(args[1])
                if result:
                    await ctx.send("It exists!")
                else:
                    await ctx.send("It does not :(")
                    return

            if args[0] == "ue" and len(args) > 1:
                await ctx.send("Checking...")
                result = db.user_exists(args[1])
                if result:
                    await ctx.send("It exists!")
                else:
                    await ctx.send("It does not :(")
                    return

            if args[0] == "gue" and len(args) > 2:
                await ctx.send("Checking...")
                result = db.user_guild_exists(args[1], args[2])
                if result:
                    await ctx.send("It exists!")
                else:
                    await ctx.send("It does not :(")
                    return

            if args[0] == "alter":
                await ctx.send("Altering...")
                db.alter()
                await ctx.send("Altered!")
                return

            if args[0] == "rg":
                await ctx.send("Resetting guild settings...")
                db.default_settings(str(ctx.guild.id))
                await ctx.send("Reset!")
                return

            if args[0] == "ggs":
                await ctx.send("Getting settings...")
                message = "```JSON\n{}\n```"
                message = message.format(json.dumps(db.get_settings(str(ctx.guild.id)), indent=4, sort_keys=True))
                await ctx.send(message)
                return

            if args[0] == "run":
                await ctx.send("Running command...")
                db.send_commands([' '.join(args[1:])])
                await ctx.send("Ran!")
                return

            await ctx.send("Unknown command...")
        else:
            await ctx.send("You're not my owner!")


def setup(bot):
    bot.add_cog(Commands(bot))
