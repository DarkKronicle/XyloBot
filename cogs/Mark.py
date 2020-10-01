from util.DiscordUtil import *
from storage.Database import *
from storage import Cache
import discord
from discord.ext import commands


class Mark(commands.Cog):

    @commands.group(name="markconfig")
    async def config(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Markconfig Help",
                description="Config your marks!",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`list <page>`", value="List what marks are for your server.")
            await ctx.send(embed=embed)

    @config.command(name="list")
    async def mark_list(self, ctx: commands.Context, *args):
        db = Database()
        rows = db.get_marks(str(ctx.guild.id))
        page = 1
        if len(args) > 0:
            try:
                page = int(args[0])
            except ValueError:
                await ctx.send("You didn't enter a proper page number!")
                return

        # 28 entries, page 2. start = 21, end = 30
        end = page * 10 - 1
        start = page * 10 - 10
        newrows = rows[start:end]
        embed = discord.Embed(
            title="Marks!",
            colour=discord.Colour.green()
        )

        if len(newrows) == 0:
            embed.add_field(name=f"No marks on {str(page)}", value="Sad day :(")
            await ctx.send(embed=embed)
            return

        current = start + 1
        for row in newrows:
            name = row[0]
            embed.add_field(name=f"{str(current)}.", value=name)
            current = current + 1
        await ctx.send(embed=embed)

    @commands.group(name="mark")
    async def mark(self, ctx: commands.Context, *args):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Markconfig Help",
                description="Config your marks!",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Mark())
