from discord.ext import commands, menus

from storage import db
from util.context import Context
from util.paginator import SimplePages


class ClipStorage(db.Table, table_name="clip_storage"):
    id = db.PrimaryKeyColumn()
    user_id = db.Column(db.Integer(big=True))
    name = db.Column(db.String(length=100))
    content = db.Column(db.String(length=2000))
    uses = db.Column(db.Integer(), default=0)

    @classmethod
    def create_table(cls, *, overwrite=False):
        statement = super().create_table(overwrite=overwrite)
        # create the unique index for guild_id and user_id for SPPEEEEEEDDD
        sql = "CREATE UNIQUE INDEX IF NOT EXISTS clip_storage_uniq_idx ON clip_storage (user_id, name);"
        return statement + '\n' + sql


# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/tags.py#L37
class ClipPageEntry:
    def __init__(self, entry):
        self.id = entry['id']
        self.name = entry['name']

    def __str__(self):
        return f"{self.name} (ID: {self.id})"


class ClipPages(SimplePages):

    def __init__(self, entries, *, per_page=15):
        converted = [ClipPageEntry(entry) for entry in entries]


# Inspired between a mix of RoboDanny and bot reminders.
# ClipName was used from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/tags.py#L114
class ClipName(commands.clean_content):
    characters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
                  "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "-", "_", "!", "/", "1", "2",
                  "3", "4", "5", "6", "7", "8", "9", "0", "@", "#", " "]

    async def convert(self, ctx, argument):
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument("You need to specify a name.")

        if len(lower) > 100:
            raise commands.BadArgument("Clip name cannot be longer than 100 characters.")

        if not all(c in self.characters for c in lower):
            raise commands.BadArgument("Not allowed characters! You can use `<a-z> <0-9> - _ ! / 1 2 3 4 5 6 7 8 9 0 "
                                       "@ #`")

        first_word, _, _ = lower.partition(' ')
        root = ctx.bot.get_command('clip')
        if first_word in root.all_commands:
            raise commands.BadArgument("This clip name starts with a reserved word.")

        return lower


class Clip(commands.Cog):
    """
    Keep track of notes and text.
    """

    def __init__(self, bot):
        self.bot = bot

    async def get_clip(self, user_id, name):
        command = "SELECT content, uses FROM clip_storage WHERE user_id={0} AND name=$${1}$$;"
        command = command.format(user_id, name)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
        return row

    @commands.group(name="clip", aliases=["c", "cp"], invoke_without_command=True)
    async def clip_command(self, ctx: Context, *, name: ClipName = None):
        """
        Store data inside of Xylo for future use!
        """
        if name is None:
            return await ctx.send_help('clip')
        clip = await self.get_clip(ctx.author.id, name)
        if clip is None:
            return await ctx.send("No clip with that name found.")
        await ctx.send(clip['content'])

    max_amount = 20

    # @clip_command.command(name="add", aliases=["new"])
    # async def add_clip(self, ctx: Context, name: ClipName = None, *, content):

    @clip_command.command(name="make", aliases=["create"])
    async def new_clip(self, ctx: Context):
        """
        Create a new clip or modify an old one.
        """
        converter = ClipName()
        original = ctx.message
        name = await ctx.raw_ask("What name will this have?")
        if name is None:
            return await ctx.timeout()
        ctx.message = name
        name = await converter.convert(ctx, name.content)
        content = await ctx.raw_ask("What will this clip say?")
        if content is None:
            return await ctx.timeout()
        ctx.message = original
        content = await ctx.clean(message=content, escape_roles=True, escape_mentions=False)
        if len(content) > 2000:
            return await ctx.send("Too long!")
        command = "INSERT INTO clip_storage(user_id, name, content) VALUES ({0}, $comm${1}$comm$, $comm${2}$comm$)" \
                  "ON CONFLICT (user_id, name) DO UPDATE SET content = EXCLUDED.content;"
        command = command.format(str(ctx.author.id), name, content)
        amount = "SELECT COUNT(*) FROM clip_storage WHERE user_id={0};"
        amount = amount.format(ctx.author.id)
        async with db.MaybeAcquire() as con:
            con.execute(amount)
            count = con.fetchone()
            if count is not None:
                num = count['count']
                if num >= self.max_amount:
                    return await ctx.send(f"You have too many clips! Use `{ctx.prefix}clip delete` to free up space.")
            con.execute(command)
        await ctx.send("Clip has been updated/created!")

    @clip_command.command(name="delete")
    async def del_clip(self, ctx: Context):
        """
        Delete a clip.
        """
        name = await ctx.ask("What name will this have?")
        if name is None:
            return await ctx.timeout()
        if not all(c in self.characters for c in name):
            return await ctx.send("You can only only use `<a-z> <0-9> - _ ! /` in the name.")
        if len(name) > 100:
            return await ctx.send("The name is too long!")
        command = "DELETE FROM clip_storage WHERE user_id={0} AND name=$${1}$$;"
        command = command.format(str(ctx.author.id), name)
        async with db.MaybeAcquire() as con:
            con.execute(command)
        await ctx.send("Deleted!")

    @clip_command.command(name="list")
    async def list_clip(self, ctx: Context):
        command = "SELECT id, name FROM clip_storage WHERE user_id={0};"
        command = command.format(ctx.author)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            entries = con.fetchall()

        if entries is None:
            return await ctx.send("No clips found.")

        try:
            p = ClipPages(entries=entries)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Clip(bot))
