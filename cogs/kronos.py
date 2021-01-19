import discord
from discord.ext import commands

from util.context import Context
from xylo_bot import XyloBot


class Kronos(commands.Cog):

    COLORS = {
        'magenta': (801129670686670958, 797200035497508864),
        'light green': (801129610103488512, 797199950457995285),
        'red': (801129569120944148, 753735598854111334),
        'purple': (801129528311021578, 753735538938216589),
        'blue': (801129463600906281, 774042634230300702),
        'green': (801129367048552488, 753735468474171402),
        'gray': (801129298836324402, 753735663135752222)
    }

    def __init__(self, bot):
        self.bot: XyloBot = bot
        self.guild: discord.Guild = self.bot.get_guild(753693459369427044)
        self.roles = {}
        self.required = {}
        for name, discord_id in self.COLORS.items():
            self.roles[name] = self.guild.get_role(discord_id[0])
            self.required[name] = self.guild.get_role(discord_id[1])

    @commands.command(name="color", hidden=True)
    async def color(self, ctx: Context, *, color=None):
        if color is None or len(color) == 0:
            description = ""
            for name in self.COLORS:
                description = description + f"`{name}` {self.roles[name].mention} {self.required[name].mention}\n"
            description = description + "`none` Removes your colors"
            embed = discord.Embed(
                title="Colors",
                description=description,
                colour=discord.Colour.blue()
            )
            embed.set_footer(text="Use >color <name> to add a color")
            await ctx.send(embed=embed)
            return
        c = color.lower()
        if c == "none":
            await ctx.author.remove_roles(*list(self.roles.values()), reason="Color")
            return await ctx.send("You don't have a color role anymore!")
        if c not in self.COLORS:
            return await ctx.send("That's not a proper color!")

        require = self.required[c]
        role = self.roles[c]
        author: discord.Member = ctx.author
        if require not in author.roles:
            return await ctx.send("You haven't unlocked that color yet!")

        await author.remove_roles(*list(self.roles.values()), reason="Color")
        await author.add_roles(role)
        await ctx.send(f"You now have the `{c}` color!")

    async def cog_check(self, ctx: Context):
        return ctx.guild.id is self.guild.id


def setup(bot):
    bot.add_cog(Kronos(bot))
