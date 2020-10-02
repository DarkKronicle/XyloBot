from util.discord_util import *
from storage.database import *
import discord
from discord.ext import commands
import asyncio


class Mark(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(name="marks")
    async def marks(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Marks Help",
                description="Config your marks!",
                colour=discord.Colour.purple()
            )
            embed.add_field(name="`list <page>`", value="List what marks are for your server.")
            embed.add_field(name="`add`", value="Starts a mark setup wizard.")
            embed.add_field(name="`remove`", value="Starts a mark remove wizard.")
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
            embed.add_field(name=f"{str(current)}.", value=name, inline=False)
            current = current + 1
        await ctx.send(embed=embed)

    @marks.command(name="remove")
    @is_allowed()
    async def remove(self, ctx: commands.Context):
        channel = ctx.channel
        prompt = None
        try:
            guild = str(ctx.guild.id)
            if await self.bot.is_owner(ctx.author):
                prompt = await channel.send("Is this a global mark? Answer `yes` or `no`")
                answer = await self.bot.wait_for(
                    "message",
                    timeout=60,
                    check=lambda msg: msg.author == ctx.author and msg.channel == channel
                )
                if answer:
                    if "yes" in answer.content:
                        guild = "global"
                else:
                    await ctx.send("Error in sending information")
                    return
            prompt = await channel.send("What name is the mark you are going to remove? You may use `a-z - _`")
            answer = await self.bot.wait_for(
                "message",
                timeout=60,
                check=lambda msg: msg.author == ctx.author and msg.channel == channel
            )
            await prompt.delete()
            await answer.delete()
            db = Database()
            if answer:
                if db.get_mark(guild, answer.content) is None:
                    await ctx.send("That mark doesn't exist!")
                    return
                db.remove_mark(guild, answer.content)
                await ctx.send(f"`{answer.content}` mark removed!")
                return
            else:
                await ctx.send("Error sending information")
                return

        except asyncio.TimeoutError:
            await prompt.delete()
            await channel.send("This has been closed due to a timeout", delete_after=15)

    characters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
                  "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "-", "_", "!", "/", "1", "2",
                  "3", "4", "5", "6", "7", "8", "9", "0", "@", "#"]

    @marks.command(name="add")
    @is_allowed()
    async def add(self, ctx: commands.Context):
        prompt = None
        details = {}
        channel = ctx.channel
        try:
            prompt = await channel.send("What name is the mark going to have? You may use `a-z - _`")
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
                elif Database().get_mark(str(ctx.guild.id), answer.content):
                    await ctx.send("That mark already exists!")
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
                return
            prompt = await ctx.send(
                "What files are going to be sent with it? (Type `none` or use URL's and seperate with `,`)")
            answer = await self.bot.wait_for(
                "message",
                timeout=60,
                check=lambda msg: msg.author == ctx.author and msg.channel == channel
            )
            await prompt.delete()
            await answer.delete()
            if answer:
                # TODO check for correct urls. Just gonna hope people aren't doofuses for now...
                if answer.content == "none":
                    details["links"] = []
                else:
                    details["links"] = answer.content.split(',')
            else:
                await ctx.send("Message was sent incorrectly!")
                return

            if await self.bot.is_owner(ctx.author):
                prompt = await channel.send("Is this going to be a global mark? `yes` or `no`")
                answer = await self.bot.wait_for(
                    "message",
                    timeout=60,
                    check=lambda msg: msg.author == ctx.author and msg.channel == channel
                )
                await prompt.delete()
                await answer.delete()
                if answer:
                    if "yes" in answer.content:
                        details["guild"] = "global"
                        db = Database()
                        if db.get_mark_named(details["name"]) is not None:
                            await ctx.send("There is already a mark in other servers named that.")
                            return
                    else:
                        details["guild"] = str(ctx.guild.id)
                else:
                    await ctx.send("Error sending information!")
                    return

            else:
                details["guild"] = str(ctx.guild.id)

            embed = discord.Embed(
                title=details["name"],
                description="Does this information look correct? Type `yes` or `no`",
                colour=discord.Colour.blue()
            )
            embed.add_field(name="Text", value=details["text"])
            if len(details["links"]) != 0:
                embed.add_field(name="Files", value=details["links"])
            prompt = await ctx.send(embed=embed)
            answer = await self.bot.wait_for(
                "message",
                timeout=60,
                check=lambda msg: msg.author == ctx.author and msg.channel == channel
            )
            await prompt.delete()
            await answer.delete()
            if answer:
                if "yes" not in answer.content:
                    await ctx.send("Start again from the beginning!", delete_after=15)
                    return
            else:
                await ctx.send("message was sent incorrectly!")
                return

            db = Database()
            db.add_mark(details["guild"], details["name"], details["text"], details["links"])
            await ctx.send("New mark added!")
            return

        except asyncio.TimeoutError:
            await prompt.delete()
            await channel.send("This has been closed due to a timeout", delete_after=15)

    @commands.command(name="mark")
    async def mark(self, ctx: commands.Context, *args):
        if len(args) == 0 or args[0] == "help":
            embed = discord.Embed(
                title="Markconfig Help",
                description="Config your marks!",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)

        name = ' '.join(args)
        db = Database()
        mark = db.get_mark(str(ctx.guild.id), name)
        if mark is not None:
            text = mark["text"]
            files = mark["files"]
            images = []
            if len(files) != 0:
                for url in files:
                    image = await get_file_from_image(url, "content.png")
                    if image is not None:
                        images.append(image)

            if len(images) != 0:
                await ctx.send(content=text, files=images)
                return
            else:
                await ctx.send(text)
                return
        await ctx.send("Mark not found!")


def setup(bot):
    bot.add_cog(Mark(bot))
