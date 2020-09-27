import discord
from util.DiscordUtil import *
from storage.Database import *
from discord.ext import commands
from discord.ext.commands import bot, has_permissions
from storage import Cache


class Customization(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="storage")
    @has_permissions(administrator=True)
    async def storage(self, ctx: commands.Context, *args):
        author: discord.Member = ctx.author
        if len(args) == 0:
            help_message = discord.Embed(
                title="Storage Commands",
                description="Keep useful info and settings.",
                colour=discord.Colour.purple()
            )
            help_message.add_field(name="`start`", value="Create an entry for your server.")
            help_message.add_field(name="`prefix`", value="Configure the server prefix!")
            await ctx.send(embed=help_message)
            return

        if args[0] == "start":
            if len(args) == 1 or len(args) >= 3:
                embed = discord.Embed(
                    title="Incorrect Usage",
                    description="`storage start <PREFIX>`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
                return

            db = Database()
            if db.guild_exists(str(ctx.guild.id)):
                await ctx.send("Guild already has data!")
                return

            db.new_guild(str(ctx.guild.id), args[1])
            await ctx.send("Created!")

        if args[0] == "prefix":
            if len(args) == 1:
                embed = discord.Embed(
                    title="Incorrect Usage",
                    description="`storage prefix <PREFIX>`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
                return

            prefix = ' '.join(args[1:])
            if len(prefix) > 15:
                await ctx.send("Prefix too large!")
                return

            if "$" in prefix:
                prefix = prefix.replace("$", "\\$")

            db = Database()
            db.set_prefix(str(ctx.guild.id), prefix)
            success = discord.Embed(
                title="Xylo prefix changed!",
                description=f"Prefix changed to `{prefix}`!",
                colour=discord.Colour.green()
            )
            Cache.clear_prefix_cache(ctx.guild)
            await ctx.send(embed=success)
            return

        if args[0] == "setup":
            if len(args) == 1:
                embed = discord.Embed(
                    title="`storage setup view`"
                )



def setup(bot):
    bot.add_cog(Customization(bot))