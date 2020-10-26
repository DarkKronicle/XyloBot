from discord.ext import commands

from storage import db
from util.context import Context


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


class Clip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def get_clip(self, user_id, name):
        command = "SELECT content, uses FROM clip_storage WHERE user_id={0} AND name=$${1}$$;"
        command = command.format(user_id, name)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            row = con.fetchone()
        return row

    @commands.group(name="clip", aliases=["c", "cp"])
    async def clip_command(self, ctx: Context):
        """
        Store data inside of Xylo for future use!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('clip')

    characters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
                  "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "-", "_", "!", "/", "1", "2",
                  "3", "4", "5", "6", "7", "8", "9", "0", "@", "#"]

    max_amount = 20

    @clip_command.command(name="new")
    async def new_clip(self, ctx: Context):
        """
        Create a new clip or modify an old one.
        """
        name = await ctx.ask("What name will this have?")
        if name is None:
            return await ctx.timeout()
        if not all(c in self.characters for c in name):
            return await ctx.send("You can only only use `<a-z> <0-9> - _ ! /` in the name.")
        if len(name) > 100:
            return await ctx.send("The name is too long!")
        content = await ctx.raw_ask("What will this clip say?")
        if content is None:
            return await ctx.timeout()
        content = content.clean_content
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

    @clip_command.command(name="clip")
    async def send_clip(self, ctx: Context, *args):
        if len(args) == 0:
            return await ctx.send("Make sure to specify a clip!")
        name = ' '.join(args)
        if not all(c in self.characters for c in name):
            return await ctx.send("You can only only use `<a-z> <0-9> - _ ! /` in the name.")
        if len(name) > 100:
            return await ctx.send("The name is too long!")
        clip = await self.get_clip(ctx.author.id, name)
        if clip is None:
            return await ctx.send("No clip with that name found.")
        await ctx.send(clip['content'])


def setup(bot):
    bot.add_cog(Clip(bot))
