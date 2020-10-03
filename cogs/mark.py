from util.discord_util import *
from storage.database import *
import discord
from discord.ext import commands
from util.context import Context


class Mark(commands.Cog):
    """
    Mess around with marks!
    """

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(name="marks")
    async def marks(self, ctx: commands.Context):
        """
        Configure and view marks
        """
        if ctx.invoked_subcommand is None:
            # embed = discord.Embed(
            #     title="Marks Help",
            #     description="Config your marks!",
            #     colour=discord.Colour.purple()
            # )
            # embed.add_field(name="`list <page>`", value="List what marks are for your server.")
            # embed.add_field(name="`add`", value="Starts a mark setup wizard.")
            # embed.add_field(name="`remove`", value="Starts a mark remove wizard.")
            # await ctx.send(embed=embed)
            await ctx.show_help()

    @marks.command(name="list", usage="<page>")
    async def mark_list(self, ctx: commands.Context, page: int):
        """
        List the current marks.
        """
        db = Database()
        rows = db.get_marks(str(ctx.guild.id))
        if page < 1:
            page = 1

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
    async def remove(self, ctx: Context):
        guild = str(ctx.guild.id)
        if await self.bot.is_owner(ctx.author):
            g = await ctx.prompt(embed=discord.Embed(title="Is this a global mark?", description="`yes` or `no`"))
            if g is None:
                await ctx.timeout()
                return
            if g:
                guild = "global"
        answer = await ctx.ask(embed=discord.Embed(title="What name is the mark?", description="You may use `a-z - _`"))
        if answer is None:
            await ctx.timeout()
            return

        db = Database()
        if db.get_mark(guild, answer) is None:
            await ctx.send("That mark doesn't exist!")
            return
        db.remove_mark(guild, answer)
        await ctx.send(f"`{answer.content}` mark removed!")
        return

    characters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
                  "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "-", "_", "!", "/", "1", "2",
                  "3", "4", "5", "6", "7", "8", "9", "0", "@", "#"]

    @marks.command(name="add")
    @is_allowed()
    async def add(self, ctx: Context):
        details = {}
        channel = ctx.channel
        prompt = await channel.send("What name is the mark going to have? You may use `a-z - _`")
        answer = await ctx.ask(embed=discord.Embed(title="What is the mark name?", description="You can use `a-z "
                                                                                               "0-9 - _ /`"))
        if answer is None:
            await ctx.timeout()
            return

        if not all(c in self.characters for c in answer):
            await ctx.send("You're not allowed to use some of those characters! `a-z - _`")
            return
        elif Database().get_mark(str(ctx.guild.id), answer):
            await ctx.send("That mark already exists!")
            return
        else:
            details["name"] = answer
        answer = await ctx.ask(embed=discord.Embed(title="What is the mark going to say?"))
        if answer is None:
            await ctx.timeout()
            return
        details["text"] = answer
        answer = await ctx.ask(embed=discord.Embed(title="What files are going to be sent?",
                                                   description="Type `none` or use URL's and separate with `,`"),
                               allow_none=True)
        if answer is None:
            await ctx.timeout()
            return
        # TODO check for correct urls. Just gonna hope people aren't doofuses for now...
        if answer == False:
            details["links"] = []
        else:
            details["links"] = answer.split(',')

        if await self.bot.is_owner(ctx.author):
            answer = await ctx.prompt(
                embed=discord.Embed(title="Is this going to be a global mark?", description="`yes` or `no`"))
            if answer is None:
                await ctx.timeout()
                return
            if answer:
                details["guild"] = "global"
                db = Database()
                if db.get_mark_named(details["name"]) is not None:
                    await ctx.send("There is already a mark in other servers named that.")
                    return
            else:
                details["guild"] = str(ctx.guild.id)

        else:
            details["guild"] = str(ctx.guild.id)

        embed = discord.Embed(
            title="Does this information look correct?",
            description="Type `yes` or `no`",
            colour=discord.Colour.blue()
        )
        embed.add_field(name="Name", value=details["name"])
        embed.add_field(name="Text", value=details["text"])
        if len(details["links"]) != 0:
            embed.add_field(name="Files", value=details["links"])
        answer = await ctx.prompt(embed=embed)

        if answer is None:
            await ctx.timeout()
            return
        if not answer:
            await ctx.send("Start again from the beginning!", delete_after=15)
            return

        db = Database()
        db.add_mark(details["guild"], details["name"], details["text"], details["links"])
        await ctx.send("New mark added!")
        return

    @commands.command(name="mark", usage="mark <name>")
    async def mark(self, ctx: commands.Context, *args):
        """
        Gets a mark from 'mark list' and prints it out into the current channel.
        """
        if len(args) == 0 or args[0] == "help":
            embed = discord.Embed(
                title="Markconfig Help",
                description="Config your marks!",
                colour=discord.Colour.purple()
            )
            await ctx.send(embed=embed)
            return
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
