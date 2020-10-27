from datetime import datetime

from storage import db
from util.context import Context
from util.discord_util import *
from discord.ext.commands import has_permissions
import json


def check_admin(ctx, **perms):
    ch = ctx.channel
    permissions = ch.permissions_for(ctx.author)

    missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

    if not missing:
        return True

    return False


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


class UserData(db.Table, table_name="user_data"):
    guild_id = db.Column(db.Integer(big=True), primary_key=True)
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    info = db.Column(db.JSON())

    @classmethod
    def create_table(cls, *, overwrite=False):
        statement = super().create_table(overwrite=overwrite)
        # create the unique index for guild_id and user_id for SPPEEEEEEDDD
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS user_data_uniq_idx ON user_data (guild_id, user_id);"
        return statement + '\n' + sql


class DataCommands(commands.Cog):
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

    limits = {
        "first": 20,
        "last": 20,
        "school": 30,
        "extra": 200,
        "birthday": 10
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_user(self, guild_id, user_id):
        command = "SELECT info FROM user_data WHERE guild_id = {} and user_id = {};"
        command = command.format(guild_id, user_id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
        if row is not None:
            return row['info']
        return row

    async def update_user(self, guild_id, user_id, info):
        command = "UPDATE user_data SET info = $${2}$$ WHERE guild_id = {0} and " \
                  "user_id = {1};"
        command = command.format(guild_id, user_id, json.dumps(info))

    @commands.command(name="whoami")
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def whoami(self, ctx: commands.Context):
        """
        Grabs data stored in the database about the sender.
        """

        v = self.bot.get_cog('Verify')
        c = await v.get_verify_config(ctx.guild.id)
        if not c.active:
            return

        id = ctx.message.author.id
        data = await self.get_user(ctx.guild.id, id)

        if data is None:
            embed = discord.Embed(
                title="Not found...",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )

        else:
            message = f"`{ctx.author.name}`:"
            for f in data["fields"]:
                message = message + f"\n-   `{self.names[f]}`: {data['fields'][f]}"

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
        v = self.bot.get_cog('Verify')
        c = await v.get_verify_config(ctx.guild.id)
        if not c.active:
            return

        if user is None:
            await ctx.send_help('whois')
            return

        data = await self.get_user(ctx.guild.id, user.id)

        if data is None:
            embed = discord.Embed(
                title="Not found!",
                description="Talk to a staff member if you believe this is an error.",
                colour=discord.Colour.red()
            )
        else:
            message = f"`{user.name}`:"
            for f in data["fields"]:
                message = message + f"\n-   `{self.names[f]}`: {data['fields'][f]}"
            await ctx.send(message)
            return

        await ctx.send(embed=embed)

    @commands.command(name="edit")
    @commands.guild_only()
    async def edit(self, ctx: Context, *args):
        """
        Edit information on people. User's can only edit their own fields that do not take place in verification.

        Values you can use are first, last, school, extra, and birthday.
        """
        admin = check_admin(ctx, administrator=True)
        member = ctx.author
        if len(args) < 2:
            await ctx.send_help('edit')
        if args[0] not in self.names:
            return await ctx.send("Specify a correct field.")

        field = args[0]
        if not admin:
            v = self.bot.get_cog('Verify')
            c = await v.get_verify_config(ctx.guild.id)
            fields = c.fields
            allowed = True
            for cfield in fields:
                if fields[cfield] and field == cfield:
                    allowed = False
                    break
            if not allowed:
                return await ctx.send("You're not allowed to change that value! Ask a staff member to change it.")
        limit = self.limits[field]
        data = ' '.join(args[1:])
        if len(data) > limit:
            return await ctx.send("Content is too big! Make it smaller.")
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
        if not answer:
            return await ctx.send("Your response has been trashed.")

        user_data = await self.get_user(ctx.guild.id, member.id)
        if "fields" not in user_data:
            user_data["fields"] = {}
        user_data["fields"][field] = data
        await self.update_user(ctx.guild.id, member.id, user_data)
        log = await ctx.bot.get_log_channel(ctx.guild)

        await ctx.send(f"Edited your {field}!")
        if log is not None:
            log_embed = discord.Embed(
                title="Data Changed",
                description=f"{member.mention} changed their data.\n\nFrom `{field}` to:\n\n{data}"
            )
            await log.send(embed=log_embed)

    @commands.command(name="editother")
    @commands.guild_only()
    @has_permissions(administrator=True)
    async def editother(self, ctx: Context, member: discord.Member = None):
        """
        Edit information other information. You need to be an admin.

        Values you can use are first, last, school, extra, and birthday.
        """
        if member is None:
            return await ctx.send("You need to specify a user to edit!")

        field = await ctx.ask("What field do you want to change?")
        if field is None:
            return await ctx.timeout()
        if field not in self.names:
            return await ctx.send("Not a proper field!")
        limit = self.limits[field]
        data = await ctx.ask("What do you want to change it to?")
        if data is None:
            return await ctx.timeout()
        if len(data) > limit:
            return await ctx.send("Content is too big! Make it smaller.")
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
        if not answer:
            return await ctx.send("Your response has been trashed.")

        user_data = await self.get_user(ctx.guild.id, member.id)
        if "fields" not in user_data:
            user_data["fields"] = {}
        user_data["fields"][field] = data
        await self.update_user(ctx.guild.id, member.id, user_data)
        log = await ctx.bot.get_log_channel(ctx.guild)

        await ctx.send(f"Edited your {field}!")
        if log is not None:
            log_embed = discord.Embed(
                title="Data Changed",
                description=f"{ctx.author.mention} changed {member.mention}'s data.\n\nFrom `{field}` to:\n\n{data}"
            )
            await log.send(embed=log_embed)


def setup(bot):
    bot.add_cog(DataCommands(bot))
