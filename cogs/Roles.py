from discord.ext import commands
from discord.ext.commands import Bot
from util.DiscordUtil import *
from storage.Config import *


class Role:

    def __init__(self, title: str, description: str, role: str, required: str):
        self.title = title
        self.description = description
        self.role = role
        self.required = required


def get_roles(guild: discord.Guild):
    config = ConfigData.rolestorage
    roles = get_keys(config.data, str(guild.id))
    if roles is None:
        return None
    role_list = []
    for role in roles:
        data = get_keys(roles, role)
        role_list.append(Role(get_keys(data, "title"), get_keys(data, "description"), get_keys(data, "role"),
                              get_keys(data, "required")))
    return role_list


class Roles(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="role")
    async def role_command(self, ctx: commands.Context, *args):
        guild: discord.Guild = ctx.guild
        roles = get_roles(guild)
        if roles is None:
            error = discord.Embed(
                title="No Roles",
                description="Looks like there are no roles for this Discord!",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=error)
            return

        if len(args) <= 0 or args[0] == "help":
            help = discord.Embed(
                title="Role Help",
                description="Get yourself some roles!",
                colour=discord.Colour.green()
            )
            help.add_field(name="list", value="View what roles there are that you can get!")
            await ctx.send(embed=help)
            return

        if args[0] == "list":
            role_embed = discord.Embed(
                title="Roles!",
                description=f"Here are the roles you can use in {guild.name}!",
                colour=discord.Colour.blue()
            )
            for role in roles:
                role_embed.add_field(name=role.title, value=role.description)

            await ctx.send(embed=role_embed)
            return

        if args[0] == "toggle":
            if len(args) < 2:
                error = discord.Embed(
                    title="Incorrect Usage",
                    description="`>roles toggle <role>`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=error)
                return

            role = None

            name: str = args[1]
            for r in roles:
                if name.lower() == r.title.lower():
                    role = get_role(r.role, guild, self.bot)
                    break

            if role is None:
                not_found = discord.Embed(
                    title="Role Not Found",
                    description="Try a different role from `>roles list`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=not_found)
                return

            if role in ctx.author.roles:
                await ctx.send(f"Removing the role `{name}`")
                await ctx.author.remove_roles(role)
            else:
                await ctx.send(f"Adding the role `{name}`")
                await ctx.author.add_roles(role)


def setup(bot):
    bot.add_cog(Roles(bot=bot))
