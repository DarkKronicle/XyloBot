import enum
import re

import typing

from discord.ext import tasks

from storage import db
from util import storage_cache, checks
from util.context import Context
from util.discord_util import *

all_emojis: dict = JSONReader("data/emojis.json").data


class StandardEmoji(commands.Converter):
    async def convert(self, ctx, argument):
        """
        # 1 - Check if unicode emoji
        # 2 - Check if it's name is in discord found
        """

        if argument in all_emojis.values():
            return argument

        argument = argument.lower()
        if argument in all_emojis.keys():
            return all_emojis[argument]

        return None


class AutoReactionsDB(db.Table, table_name="auto_reactions"):
    id = db.Column(db.Integer(big=True, auto_increment=True), primary_key=True)
    guild_id = db.Column(db.Integer(big=True), index=True)
    name = db.Column(db.String(length=50), primary_key=True)
    filter = db.Column(db.String(length=50))
    # 0 case sensitive anywhere.
    # 1 case insensitive anywhere.
    # 2 case sensitive only.
    # 3 case insensitive only.
    filter_type = db.Column(db.Integer(small=True))

    reaction = db.Column(db.String(length=500))
    # 0 Emojis
    # 1 Text
    reaction_type = db.Column(db.Integer(small=True))

    uses = db.Column(db.Integer(), default=0)


class FilterType(enum.Enum):
    # Filter: BRO   Example: What the heck bro?   Result: True
    sensitive_any = 0
    # Filter: BRO   Example: What the heck bro?   Result: False
    insensitive_any = 1
    # Filter: BRO   Example: bro   Result: True
    sensitive_only = 2
    # Filter: BRO   Example: WHY BRO??   Result: False
    insensitive_only = 3

    @classmethod
    def human_readable(cls, type):
        if type == FilterType.sensitive_any:
            return "Found anywhere, case sensitive."
        if type == FilterType.insensitive_any:
            return "Found anywhere, case insensitive."
        if type == FilterType.sensitive_only:
            return "Only filter, case sensitive."
        if type == FilterType.insensitive_only:
            return "Only filter, case insensitive."
        return "Error"


class ReactionType(enum.Enum):
    # React by using reactions
    reaction = 0
    # React using text.
    text = 1

    @classmethod
    def human_readable(cls, type):
        if type == ReactionType.reaction:
            return "Emoji Reaction."
        if type == ReactionType.text:
            return "Separate message."
        return "Error"


class AutoReactionConfig:
    class ReactionData:
        """
        Stores how it will react to data.
        """

        def __init__(self, id, name, filter, data, *, ftype=1, rtype=0,
                     uses=0):
            self.id = id
            self.name = name
            self.ftype = ftype
            self.filter = filter
            self.data = data
            self.rtype = rtype
            self.uses = uses
            self._uses = uses

        def add(self):
            self._uses = self._uses + 1

        def get_uses(self):
            return self.uses + self._uses

        def get_data(self):
            if self.reaction_type == ReactionType.reaction:
                return self.data.split(',')
            return self.data

        def filtered(self, message):
            """
            Checks to see if a message will get filtered.
            :param message: The message to check if it will filter.
            :return: True if it matches, False if not.
            """
            f = self.filter_type
            if f == FilterType.sensitive_any:
                if self.filter in message:
                    return True
            elif f == FilterType.insensitive_any:
                if self.filter.lower() in message.lower():
                    return True
            elif f == FilterType.sensitive_only:
                if self.filter == message:
                    return True
            else:
                if self.filter.lower() == message.lower():
                    return True

            return False

        @property
        def reaction_type(self):
            return ReactionType(self.rtype)

        @property
        def filter_type(self):
            return FilterType(self.ftype)

    def __init__(self, guild_id, data):
        self.reactions = []
        self.guild_id = guild_id
        if len(data) == 0:
            return
        for row in data:
            self.reactions.append(
                self.ReactionData(row['id'], row['name'], row['filter'], row['reaction'],
                                  ftype=row['filter_type'], rtype=row['reaction_type'], uses=row['uses'])
            )

    def get_reactions(self, message, *, stats=None):
        reacts = {
            "emojis": [],
            "text": []
        }
        for reaction in self.reactions:
            if reaction.filtered(message):
                if stats is not None:
                    stats[reaction.id] = reaction.get_uses()
                reaction.add()
                if reaction.reaction_type == ReactionType.reaction:
                    reacts["emojis"].extend(reaction.get_data())
                if reaction.reaction_type == ReactionType.text:
                    reacts["text"].append(reaction.get_data())

        return reacts

    async def react(self, message: discord.Message, *, stats=None):
        reacts = self.get_reactions(message.content, stats=stats)
        if len(reacts["emojis"]) != 0:
            for e in reacts["emojis"]:
                await message.add_reaction(e)
        if len(reacts["text"]) != 0:
            for t in reacts["text"]:
                await message.channel.send(t)


class AutoReactionName(commands.Converter):
    async def convert(self, ctx: Context, argument):
        ar = ctx.bot.get_cog('AutoReactions')
        if ar is None:
            return None

        reactions: AutoReactionConfig = await ar.get_autoreactions(ctx.guild.id)
        for r in reactions.reactions:
            if argument.lower() == r.name.lower():
                return r

        return None


class AutoReactions(commands.Cog):
    """
    Emojis Xylo automatically reacts to.
    """

    def __init__(self, bot):
        self.bot = bot
        self.bulk_uses = {}
        self.update_usage.start()

    @storage_cache.cache(maxsize=256)
    async def get_autoreactions(self, guild_id):
        command = "SELECT id, name, filter, filter_type, reaction, reaction_type, uses FROM auto_reactions WHERE " \
                  "guild_id={0}; "
        command = command.format(guild_id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            rows = con.fetchall()
        return AutoReactionConfig(guild_id, rows)

    @tasks.loop(minutes=5)
    async def update_usage(self):
        if len(self.bulk_uses) != 0:
            command = "UPDATE auto_reactions AS x set id = x2.id, uses = x2.uses FROM (VALUES {0}) AS x2(id, " \
                      "uses) WHERE x.id = x2.id;"
            val = "({0}, {1})"
            vals = []
            for rid in self.bulk_uses:
                uses = self.bulk_uses[rid]
                vals.append(val.format(rid, uses))
            command = command.format(', '.join(vals))
            async with db.MaybeAcquire() as con:
                con.execute(command)
            self.bulk_uses = {}

    def _bulk_add_reaction_sql(self, guild_id, data_list: list):
        insert = "INSERT INTO auto_reactions (guild_id, name, filter, filter_type, reaction, reaction_type) VALUES "
        reactions = []
        for data in data_list:
            reactions.append(f"({guild_id}, $${data.name}$$, $${data.filter}$$, "
                             f"{data.ftype}, $${data.data}$$, {data.rtype})")

        insert = insert + ', '.join(reactions) + ";"
        return insert

    async def set_defaults(self, guild_id):
        data = []
        data.append(
            AutoReactionConfig.ReactionData(0, "PANIC", "oh no", "<:panik:771175655563984897>")
        )
        data.append(
            AutoReactionConfig.ReactionData(0, "poggers", "pog", "<:pog:771175687516061726>")
        )
        data.append(
            AutoReactionConfig.ReactionData(0, "NO U", "no u", "no u", ftype=3, rtype=1)
        )
        data.append(
            AutoReactionConfig.ReactionData(0, "table u", "(╯°□°）╯︵ ┻━┻", "┬─┬ノ( º _ ºノ)", ftype=2, rtype=1)
        )
        data.append(
            AutoReactionConfig.ReactionData(0, "Xylo", "xylo", "<:shades:771180613708546048>")
        )
        data.append(
            AutoReactionConfig.ReactionData(0, "Bruh", "bruh", "<:bruh:771175714790703125>")
        )
        sql = self._bulk_add_reaction_sql(guild_id, data)
        async with db.MaybeAcquire() as con:
            con.execute(f"DELETE FROM auto_reactions WHERE guild_id={guild_id};" + "\n" + sql)
        self.get_autoreactions.invalidate(self, guild_id)

    async def add_reaction(self, guild_id, data: AutoReactionConfig.ReactionData):
        insert = "INSERT INTO auto_reactions (guild_id, name, filter, filter_type, reaction, reaction_type) VALUES (" \
                 f"{guild_id}, $${data.name}$$, $${data.filter}$$, {data.ftype}, $${data.data}$$, {data.rtype});"
        async with db.MaybeAcquire() as con:
            con.execute(insert)
        self.get_autoreactions.invalidate(self, guild_id)

    async def remove_reaction(self, guild_id, name):
        command = "DELETE FROM auto_reactions WHERE guild_id={0} AND name=$${1}$$;"
        command = command.format(guild_id, name)
        async with db.MaybeAcquire() as con:
            con.execute(command)
        self.get_autoreactions.invalidate(self, guild_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Don't want recursion now... it's the skeletons all over
        if message.author.bot:
            return

        # Guild only so we don't get into weird configurations.
        if message.guild is None:
            return

        reactions = await self.get_autoreactions(message.guild.id)
        # If it's empty, don't want to do that...
        if len(reactions.reactions) == 0:
            return

        await reactions.react(message, stats=self.bulk_uses)

    @commands.command(name="autoreactions", aliases=["ar", "autoreaction"])
    @commands.guild_only()
    async def autoreaction(self, ctx: commands.Context, autoreaction: AutoReactionName = None):
        """
        View current AutoReactions
        """
        if autoreaction is not None:
            embed = await self.get_about_embed(autoreaction)
            return await ctx.send(embed=embed)
        reactions = await self.get_autoreactions(ctx.guild.id)
        if len(reactions.reactions) == 0:
            return await ctx.send("This guild currently has no auto reactions.")
        message = f"Current reactions in this guild. Use `{ctx.prefix}ar <reaction_name>` to view more information."
        for r in reactions.reactions:
            message = message + f"\n`{r.name}`"
        await ctx.send(message)

    @commands.group(name="!autoreactions", aliases=["!autoreaction", "!ar"])
    @commands.guild_only()
    @checks.is_mod()
    async def config_autoreactions(self, ctx: Context):
        """
        Mess around with autoreactions and set them up!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('!autoreactions')

    @config_autoreactions.command(name="reset")
    @checks.is_mod()
    async def reset_ar(self, ctx: Context):
        """
        Resets auto reactions.
        """
        yes = await ctx.prompt("Are you sure you want to revert to default autoreactions? "
                               "This will delete *all* of your current ones.")
        if yes is None:
            return await ctx.timeout()
        if not yes:
            return ctx.send("Ok, not resetting!")
        await self.set_defaults(ctx.guild.id)
        await ctx.send("Reset!")

    @config_autoreactions.command(name="new", aliases=["make"])
    @commands.guild_only()
    @checks.is_mod()
    async def config_ar_new(self, ctx: Context):
        """
        Setup wizard for a new auto reaction.
        """
        reacts = await self.get_autoreactions(ctx.guild.id)
        if len(reacts.reactions) >= 20:
            return await ctx.send("You already have the maximum amount of auto reactions (10). You can delete some to "
                                  "make room for more using "
                                  f"`{ctx.prefix}!autoreactions delete`.")
        name = await ctx.ask("What name will the new auto reaction have?")
        if name is None:
            return await ctx.timeout()
        for r in reacts.reactions:
            if r.name.lower() == name.lower():
                return await ctx.send("There is already a reaction named that in this guild!")
        name = name.replace("$", r"\$")

        ftype = await ctx.ask("What type of filter will this be?\n**0.** Case sensitive and can be found anywhere."
                              "\n**1.** Case insensitive and can be found anywhere."
                              "\n**2.** Case sensitive and it has to only be that text."
                              "\n**3.** Case insensitive and it has to only be that text.")
        if ftype is None:
            return await ctx.timeout()
        try:
            ftype = int(ftype)
        except ValueError:
            return await ctx.send("You need to specify a number from 0-3.")
        if ftype > 3 or ftype < 0:
            return await ctx.send("You need to specify a number from 0-3.")

        filter = await ctx.ask("What should I look for? This can be 40 characters long.")
        if filter is None:
            return await ctx.timeout()
        if len(filter) > 40:
            return await ctx.send("Too long!")
        filter = filter.replace("$", r"\$")

        rtype = await ctx.ask("How should I react?"
                              "\n**0.** Use emojis to add a reaction."
                              "\n**1.** Respond with a message."
                              )
        if rtype is None:
            return await ctx.timeout()
        try:
            rtype = int(rtype)
        except ValueError:
            return await ctx.send("You need to specify a number from 0-1.")
        if rtype > 3 or rtype < 0:
            return await ctx.send("You need to specify a number from 0-1.")

        data = await ctx.ask("What data should I respond with? If it's reactions it has to be emojis. (Split with "
                             "spaces)")
        if data is None:
            return await ctx.timeout()
        if ReactionType(rtype) == ReactionType.reaction:
            split = data.split(' ')
            emojis = []
            for s in split:
                e = await StandardEmoji().convert(ctx, s)
                if e is not None:
                    emojis.append(e)
                    continue
                try:
                    e = await commands.EmojiConverter().convert(ctx, s)
                except commands.EmojiNotFound:
                    e = None
                if e is not None:
                    emojis.append(f"<:{e.name}:{e.id}>")
            data = ','.join(emojis)
            if len(emojis) > 10:
                return await ctx.send("Sorry, you can only add 10 emojis for a single autoreaction.")

        if len(data) > 1900:
            return await ctx.send(
                "Sorry, the data is too long. If you're using reactions maybe do smaller custom emojis.")

        final = AutoReactionConfig.ReactionData(0, name, filter, data, ftype=ftype, rtype=rtype)
        embed = await self.get_about_embed(final)
        result = await ctx.prompt("Does this look right?", embed=embed)
        if result is None:
            return await ctx.timeout()
        if not result:
            return await ctx.send("Ok, I won't add it!")

        if final.reaction_type == ReactionType.reaction:
            try:
                for e in final.get_data():
                    await ctx.message.add_reaction(e)
            except discord.errors.HTTPException:
                return await ctx.send("Looks like I couldn't find an emoji in there. Please contact my owner if you "
                                      "did everything correctly.")

        await self.add_reaction(ctx.guild.id, final)
        await ctx.send("Added reaction!")

    @config_autoreactions.command(name="delete")
    async def delete_ar(self, ctx: Context, ar: AutoReactionName = None):
        """
        Delete's an auto reaction.
        """
        if ar is None:
            return await ctx.send("Please specify a correct autoreaction.")
        embed = await self.get_about_embed(ar)
        yes = await ctx.prompt("Are you sure you want to delete this?", embed=embed)
        if yes is None:
            return await ctx.timeout()
        if not yes:
            return await ctx.send("Cancelled")
        await self.remove_reaction(ctx.guild.id, ar.name)
        await ctx.send("Removed")

    async def get_about_embed(self, data: AutoReactionConfig.ReactionData):
        embed = discord.Embed(
            title=f"AutoReaction: {data.name}",
            colour=discord.Colour.gold()
        )
        message = f"Filter Type: `{FilterType.human_readable(data.filter_type)}`\nFilter: `{data.filter}`\nResult " \
                  f"Type: `{ReactionType.human_readable(data.reaction_type)}`\nResult Data: `{data.data}`\nUses: `{data.get_uses()}`"
        embed.description = message
        return embed

    @commands.command(name="emoji")
    async def emoji(self, ctx: Context,
                    emoji_found: commands.Greedy[typing.Union[discord.Emoji, StandardEmoji]] = None):
        """
        View emojis in a text.
        """
        if emoji_found is None or len(emoji_found) == 0:
            return await ctx.send("No emoji in that text!")
        message = "Emoji's found:"
        for emoji in emoji_found:
            if emoji is not None:
                if isinstance(emoji, discord.Emoji):
                    if emoji.animated:
                        message = message + f"\n <a:{emoji.name}:{emoji.id}> - `<a:{emoji.name}:{emoji.id}>`"
                    else:
                        message = message + f"\n <:{emoji.name}:{emoji.id}> - `<:{emoji.name}:{emoji.id}>`"
                else:
                    name = ""
                    for v in all_emojis.values():
                        if v == emoji:
                            name = v
                            break

                    message = message + f"\n{name} - \\{emoji}"

        await ctx.send(message)


def setup(bot):
    bot.add_cog(AutoReactions(bot))
