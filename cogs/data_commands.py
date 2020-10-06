from datetime import datetime

import discord
from discord.ext import commands
from storage.database_helper import *
from util.context import Context
from util.discord_util import *
from storage.database import *
from discord.ext.commands import has_permissions
import json
from storage import cache


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
    """
    Commands to view stored data on people.
    """

    names = {
        "first": "First Name",
        "last": "Last Name",
        "school": "School",
        "extra": "Description",
        "birthday": "Birthday"
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="whoami")
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def whoami(self, ctx: commands.Context):
        """
        Grabs data stored in the database about the sender.
        """

        if not cache.get_enabled(ctx.guild):
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
                message = message + f"\n-   {self.names[f]}: {data['fields'][f]}"

            await ctx.send(message)
            return

        await ctx.send(embed=embed)

    @commands.command(name="whois")
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def whois(self, ctx: commands.Context, user: discord.Member = None):
        """
        Grabs data stored in the database about the specified user.
        """
        if not cache.get_enabled(ctx.guild):
            return

        if user is None:
            await ctx.send_help('whois')
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
            message = f"`{user.name}`:"
            for f in data["fields"]:
                message = message + f"\n-   {self.names[f]}: `{data['fields'][f]}`"
            await ctx.send(message)
            return

        await ctx.send(embed=embed)

    @commands.command(name="edit")
    @commands.guild_only()
    async def edit(self, ctx: Context, *args, member: discord.Member = None):
        """
        Edit information on people. User's can only edit their own fields that do not take place in verification.

        Values you can use are first, last, school, extra, and birthday.
        """
        admin = False
        if member is None:
            member = ctx.author
        else:
            if not ctx.message.author.server_permissions.administrator:
                return await ctx.send("Only admin's can change other people's values!")
            admin = True
        if len(args) < 2:
            await ctx.send_help('edit')
        if args[0] not in self.names:
            return await ctx.send("Specify a correct field.")

        field = args[0]
        if not admin:
            fields = cache.get_fields(ctx.guild)
            allowed = True
            for cfield in fields:
                if fields[cfield] and field == cfield:
                    allowed = False
                    break
            if not allowed:
                return await ctx.send("You're not allowed to change that value! Ask a staff member to change it.")
        data = ' '.join(args[1:])
        if field == "birthday":
            date_string = data
            bformat = "%Y-%m-%d"
            try:
                datetime.strptime(date_string, bformat)
            except ValueError:
                return await ctx.send("Birthday format needs to be `YYYY-MM-DD`")
        ask = discord.Embed(
            title="Edit this information?",
            description=f"{member.mention} for `{field}` to:\n\n{data}",
            colour=discord.Colour.purple()
        )
        answer = await ctx.prompt(embed=ask)
        if answer is None:
            return await ctx.timeout()

        db = Database()
        user_data = db.get_user(str(ctx.guild.id), str(member.id))
        if "fields" not in user_data:
            user_data["fields"] = user_data
        user_data["fields"]["field"] = data
        db.update_user(user_data, str(member.id), str(ctx.guild.id))
        log = cache.get_log_channel(ctx.guild)

        await ctx.send(f"Edited your {field}!")
        if log is not None:
            log_embed = discord.Embed(
                title="Data Changed",
                description=f"{ctx.author.mention} changed {member.mention}'s data.\n\nFrom `{field}` to:\n\n{data}"
            )
            await log.send(embed=log_embed)

    @commands.command(name="db", hidden=True)
    @commands.guild_only()
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
