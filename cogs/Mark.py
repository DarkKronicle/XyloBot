from util.DiscordUtil import *
from storage.Database import *
from storage import Cache
import discord
from discord.ext import commands
import asyncio


class Mark(commands.Cog):

    @commands.group(name="marks")
    async def marks(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Marks Help",
                description="Config your marks!",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`list <page>`", value="List what marks are for your server.")
            await ctx.send(embed=embed)

    @marks.command(name="list")
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

    characters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
    "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "-", "_"]

    @marks.command(name="add")
    async def add(self, ctx: commands.Context):
        details = {}
        channel = ctx.channel
        prompt = await channel.send("What name is the mark going to have? You may use `a-z - _`")
        try:
            answer = await self.bot.wait_for(
                "message",
                timeout=60,
                check=lambda msg: msg.author == ctx.author and msg.channel == channel
            )
            await prompt.delete()
            await answer.delete()
            if answer:
                if not all(c in self.characters for c in answer.content):
                    await ctx.send("You're not allowed to use some of those characters! `a-z - _`")
                    return  
                else:
                    details["name"] = answer.content
            else:
                await ctx.send("Message was sent incorrectly!", delete_after=15)
                return
            prompt = await ctx.send("What is the mark going to say?")
            answer = await self.bot.wait_for(
                "message",
                timeout=60,
                check=lambda msg: msg.author == ctx.author and msg.channel == channel
            )
            await prompt.delete()
            await answer.delete()
            if answer:
                details["text"] = answer.content
            else:
                await ctx.send("Message was sent incorrectly!", delete_after=15)
            prompt = await ctx.send("What files are going to be sent with it? (Use URL's and seperate with `,`)")
            answer = await self.bot.wait_for(
                "message",
                timeout=60,
                check=lambda msg: msg.author == ctx.author and msg.channel == channel
            )
            await prompt.delete()
            await answer.delete()
            if answer:
                # TODO check for correct urls. Just gonna hope people aren't doofuses for now...
                details["links"] = answer.content.split(',')
            else:
                await ctx.send("Message was sent incorrectly!")

            
        except asyncio.TimeoutError:
            await prompt.delete()
            await channel.send("This has been closed due to a timeout", delete_after=15)

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
