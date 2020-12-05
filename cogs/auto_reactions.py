import enum

import typing

from discord.ext import tasks, commands, menus
import random

from storage import db
from storage.json_reader import JSONReader
from util import storage_cache, checks
from util.context import Context
from util.discord_util import *
from util.paginator import SimplePageSource, Pages

all_emojis: dict = JSONReader("data/emojis.json").data

emoji_list = []

for _, emoji in all_emojis.items():
    diversity = emoji.get("diversity")
    if diversity is None:
        emoji_list.append(emoji["emoji"])
    else:
        emoji_list.append([e for _, e in emoji["diversity"].items()])

all_emoji_data: dict = {k: v["emoji"] for k, v in all_emojis.items()}


class StandardEmoji(commands.Converter):
    async def convert(self, ctx, argument):
        """
        # 1 - Check if unicode emoji
        # 2 - Check if it's name is in discord found
        """

        if argument in all_emoji_data.values():
            return argument

        argument = argument.lower()
        if argument in all_emoji_data.keys():
            return all_emoji_data[argument]

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
            self._uses = 0

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
                reaction.add()
                if stats is not None:
                    stats[reaction.id] = reaction.get_uses()
                if reaction.reaction_type == ReactionType.reaction:
                    reacts["emojis"].extend(reaction.get_data())
                if reaction.reaction_type == ReactionType.text:
                    reacts["text"].append(reaction.get_data())

        return reacts

    async def react(self, message: discord.Message, *, stats=None):
        reacts = self.get_reactions(message.content, stats=stats)
        if len(reacts["emojis"]) != 0:
            for e in reacts["emojis"]:
                try:
                    await message.add_reaction(e)
                except (discord.HTTPException, discord.Forbidden):
                    pass
        if len(reacts["text"]) != 0:
            for t in reacts["text"]:
                try:
                    await message.channel.send(t)
                except (discord.HTTPException, discord.Forbidden):
                    pass


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


class AREntrySource(SimplePageSource):

    async def format_page(self, menu, entries):
        await super().format_page(menu, entries)
        menu.embed.description = menu.embed.description + "\n\n*To see more information about a specific reaction, use `>ar " \
                                              "<name>`* "
        return menu.embed


class ARPageEntry:
    def __init__(self, entry: AutoReactionConfig.ReactionData):
        self.name = entry.name
        self.id = entry.id
        self.uses = entry.get_uses()

    def __str__(self):
        return f"{self.name} (Uses: {self.uses}, ID: {self.id})"


class ARPages(Pages):

    def __init__(self, config: AutoReactionConfig, *, per_page=15):
        converted = [ARPageEntry(entry) for entry in config.reactions]
        super().__init__(AREntrySource(converted, per_page=per_page))
        self.embed = discord.Embed(colour=discord.Colour.blurple())


class AutoReactions(commands.Cog):
    """
    Messages that Xylo will automatically react to.
    """

    def __init__(self, bot):
        self.bot = bot
        self.bulk_uses = {}
        self.update_usage.start()
        self.suffer = 350007702451126282

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
            self.bulk_uses.clear()

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
        data.append(
            AutoReactionConfig.ReactionData(0, "boi", "boi", "<a:boi:771176183290920980>")
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

        if message.guild.id == 752584642246213732 or message.guild.id == 690652919741284402:
            if self.suffer == 0 or message.author.id == self.suffer or message.channel.id == self.suffer:
                emojis = random.choice(emoji_list)
                try:
                    await message.add_reaction(emojis)
                except:
                    pass

        reactions = await self.get_autoreactions(message.guild.id)
        # If it's empty, don't want to do that...
        if len(reactions.reactions) == 0:
            return

        await reactions.react(message, stats=self.bulk_uses)

    @commands.command(name="autoreactions", aliases=["ar", "autoreaction"])
    @commands.guild_only()
    async def autoreaction(self, ctx: commands.Context, *autoreaction):
        """
        View current AutoReactions
        """
        if autoreaction is None or len(autoreaction) == 0:
            return await self.send_list_menu(ctx)

        autoreaction = await AutoReactionName().convert(ctx, ' '.join(autoreaction))

        if autoreaction is not None:
            embed = await self.get_about_embed(autoreaction)
            return await ctx.send(embed=embed)
        reactions = await self.get_autoreactions(ctx.guild.id)
        if len(reactions.reactions) == 0:
            return await ctx.send("This guild currently has no auto reactions.")
        await self.send_list_menu(ctx)

    async def send_list_menu(self, ctx):
        reactions = await self.get_autoreactions(ctx.guild.id)
        if len(reactions.reactions) == 0:
            return await ctx.send("This guild currently has no auto reactions.")
        try:
            p = ARPages(reactions)
            await p.start(ctx)
        except menus.MenuError as e:
            await ctx.send(e)

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
        if len(name) > 20:
            return await ctx.send("Name is too big!")

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
                    if e.guild.id not in (ctx.guild.id, 658371169728331788):
                        # We don't want cross guild stuff... but Xylo's server is fine.
                        continue
                    if e.animated:
                        emojis.append(f"<a:{e.name}:{e.id}>")
                    else:
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
        
    @config_autoreactions.group(name="edit")
    async def ar_edit(self, ctx: Context):
        """
        Edit data about auto reactions.
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help("!ar help")

    @ar_edit.command(name="name")
    async def edit_name(self, ctx: Context, autoreaction: AutoReactionName = None, newname: str = None):
        """
        Edit the name of an auto reaction.
        """
        if autoreaction is None:
            return await ctx.send("Please specify a correct auto reaction.")
        newname = newname.replace("$", r"\$")
        if len(newname) > 20:
            return await ctx.send("Name is too big!")
        command = "UPDATE FROM auto_reactions SET name = $${2}$$ WHERE guild_id = {0} AND name = $${2}$$;"
        command = command.format(ctx.guild.id, autoreaction.name, newname)
        async with db.MaybeAcquire() as con:
            con.execute(command)

        await ctx.send(f"`{autoreaction.name}` >>> `{newname}`")
        self.get_autoreactions.invalidate(self, ctx.guild.id)

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
        count = 0
        for emoji in emoji_found:
            if emoji is not None:
                if isinstance(emoji, discord.Emoji):
                    if emoji.guild.id not in (ctx.guild.id, 658371169728331788):
                        # We don't want cross guild stuff... but Xylo's server is fine.
                        continue
                    if emoji.animated:
                        message = message + f"\n <a:{emoji.name}:{emoji.id}> - `<a:{emoji.name}:{emoji.id}>`"
                    else:
                        message = message + f"\n <:{emoji.name}:{emoji.id}> - `<:{emoji.name}:{emoji.id}>`"
                    count = count + 1
                else:
                    name = ""
                    for v in all_emoji_data.values():
                        if v == emoji:
                            name = v
                            break

                    message = message + f"\n{name} - \\{emoji}"

        await ctx.send(message)

    @commands.command(name="react")
    async def react(self, ctx: Context, message: typing.Optional[discord.Message] = None, emojis: commands.Greedy[typing.Union[discord.Emoji, StandardEmoji]] = None):
        """
        Reacts to a message. If none specified it will react to the last message.
        """
        if emojis is None or len(emojis) == 0:
            return await ctx.send("You need to specify at least one emoji!")
        elif len(emojis) > 10:
            return await ctx.send("You can only react with 10 emojis maximum.")
        if message is None:
            one = False
            async for m in ctx.channel.history(limit=2):
                if one:
                    message = m
                    break
                else:
                    one = True
            if message is None:
                return await ctx.send("Something went wrong finding a message...")
        if await checks.check_permissions(ctx, {'add_reactions': True, 'administrator': True}, channel=message.channel, check=any):
            try:
                for emoji in emojis:
                    if emoji is None:
                        continue
                    if isinstance(emoji, discord.Emoji):
                        if emoji.guild.id not in (ctx.guild.id, 658371169728331788):
                            # We don't want cross guild stuff... but Xylo's server is fine.
                            continue
                    await message.add_reaction(emoji)
            except discord.HTTPException:
                return await ctx.send("Something went wrong!")
        else:
            return await ctx.send("You don't have permission to add reactions to that message!")

    @commands.command(name="*suffer", hidden=True)
    @checks.owner_or(332994937450921986)
    async def suffer_person(self, ctx: Context, place: typing.Union[discord.Member, discord.TextChannel] = None):
        if place is None:
            mid = 0
            human = "everyone"
        else:
            mid = place.id
            human = place.mention

        self.suffer = mid
        await ctx.send(f"Now suffering {human}.")


def setup(bot):
    bot.add_cog(AutoReactions(bot))
