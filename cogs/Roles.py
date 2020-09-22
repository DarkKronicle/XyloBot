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
        role_list.append(Role(get_keys(role, "title"), get_keys(role, "description"), get_keys(role, "role"),
                              get_keys(role, "required")))
    return role_list


class Roles(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(name="role")
    async def role_command(self, ctx: commands.Context, *args: list):
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

        if args[0] == "list":
            role_embed = discord.Embed(
                title="Roles!",
                description=f"Here are the roles you can use in {guild.name}!",
                colour=discord.Colour.blue()
            )
            for role in roles:
                role_embed.add_field(name=role.title, value=role.description)

            await ctx.send(embed=role_embed)


def setup(bot):
    bot.add_cog(Roles(bot=bot))
