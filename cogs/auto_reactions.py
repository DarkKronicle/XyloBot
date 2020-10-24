import enum
import re

import typing

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


class ReactionType(enum.Enum):
    # React by using reactions
    reaction = 0
    # React using text.
    text = 1


class AutoReactionConfig:

    class ReactionData:
        """
        Stores how it will react to data.
        """
        def __init__(self, name, filter, data, *, ftype=FilterType.sensitive_any, rtype=ReactionType.reaction, uses=0):
            self.name = name
            self.ftype = ftype
            self.filter = filter
            self.data = data
            self.rtype = rtype
            self.uses = uses

        def add(self):
            self.uses = self.uses + 1

        def get_data(self):
            if self.rtype == ReactionType.reaction:
                return self.data.split(',')
            return self.data

        def filtered(self, message):
            """
            Checks to see if a message will get filtered.
            :param message: The message to check if it will filter.
            :return: True if it matches, False if not.
            """
            if self.ftype == FilterType.sensitive_any:
                if self.filter.lower() in message.lower():
                    return True
            elif self.ftype == FilterType.insensitive_any:
                if self.filter in message:
                    return True
            elif self.ftype == FilterType.sensitive_only:
                if self.filter.lower() == message.lower():
                    return True
            else:
                if self.filter == message.lower():
                    return True

            return False

    def __init__(self, guild_id, data):
        self.reactions = []
        self.guild_id = guild_id
        if len(data) == 0:
            return
        for row in data:
            self.reactions.append(self.ReactionData(row['name'], row['filter'], row['reaction'], ftype=row['filter_type'], rtype=row['reaction_type']))

    def get_reactions(self, message):
        reacts = {
            "emojis": [],
            "text": []
        }
        for reaction in self.reactions:
            if reaction.filtered(message):
                reaction.add()
                if reaction.rtype == ReactionType.reaction:
                    reacts["emojis"].extend(reaction.get_data())
                if reaction.rtype == ReactionType.text:
                    reacts["text"].append(reaction.get_data())

        return reacts

    async def react(self, message: discord.Message):
        reacts = self.get_reactions(message.content)
        if len(reacts["emojis"]) != 0:
            for e in reacts["emojis"]:
                await message.add_reaction(e)
        if len(reacts["text"]) != 0:
            for t in reacts["text"]:
                await message.channel.send(t)


class TextType(enum.Enum):
    command = "command",
    only = "only",
    anywhere = "anywhere"


class AutoReaction:

    def __init__(self, trigger: str, reaction: list, aliases: list, case: bool):
        self.trigger = trigger
        self.reaction = reaction
        self.aliases = aliases
        self.case = case


class AutoText:

    def __init__(self, trigger: str, text: str, aliases: list, case: bool, texttype: str, files: list):
        self.trigger = trigger
        self.text = text
        self.aliases = aliases
        self.case = case
        self.files = files
        if texttype in "only":
            self.texttype = TextType.only
        elif texttype in "command":
            self.texttype = TextType.command
        else:
            self.texttype = TextType.anywhere

    async def send(self, message: discord.Message):
        file_list = []
        if len(self.files) > 0:
            for f in self.files:
                file = await get_file_from_image(f, "content.png")
                if file is not None:
                    file_list.append(file)
        if len(file_list) > 0:
            await message.channel.send(content=self.text, files=file_list)
        else:
            await message.channel.send(self.text)


class AutoReactions(commands.Cog):
    """
    Emojis Xylo automatically reacts to.
    """

    def __init__(self, bot):
        self.bot = bot

    autoreactions = ConfigData.autoreactions
    reactions = []
    texts = []
    config_reactions = autoreactions.data["reactions"]
    config_text = autoreactions.data["text"]

    for react in config_reactions:
        data = config_reactions[react]
        reactions.append(
            AutoReaction(react, get_keys(data, "emojis"), get_keys(data, "aliases"), get_keys(data, "case")))

    for text in config_text:
        data = config_text[text]
        texts.append(AutoText(text, get_keys(data, "text"), get_keys(data, "aliases"), get_keys(data, "case"),
                              get_keys(data, "type"), get_keys(data, "files")))
        # texts.append(AutoText(text, data["text"], data["aliases"], data["case"], data["type"], data["files"]))

    @storage_cache.cache(maxsize=256)
    async def get_autoreactions(self, guild_id):
        command = "SELECT name, filter, filter_type, reaction, reaction_type FROM auto_reactions WHERE guild_id={0};"
        command = command.format(guild_id)
        async with db.MaybeAcquire() as con:
            con.execute(command)
            rows = con.fetchall()
        return AutoReactionConfig(guild_id, rows)

    async def add_reaction(self, guild_id, data: AutoReactionConfig.ReactionData, *, max_amount=10):
        """
        Returns False if over max, None if it failed.
        """
        reacts = await self.get_autoreactions(guild_id)
        if len(reacts.reactions) >= max_amount:
            return False
        for r in reacts.reactions:
            if r.name.lower() == data.name.lower():
                return None
        insert = "INSERT INTO auto_reactions (guild_id, name, filter, filter_type, reaction, reaction_type) VALUES (" \
                 f"{guild_id}, $${data.name}$$, $${data.filter}$$, {data.ftype}, $${data.data}$$, {data.rtype});"
        async with db.MaybeAcquire() as con:
            con.execute(insert)
        self.get_autoreactions.invalidate(self, guild_id)
        return True

    async def remove_reaction(self, guild_id, name):
        command = "DELETE FROM auto_reactions WHERE guild_id={0} AND name={1};"
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

        await reactions.react(message)

    @commands.command(name="autoreactions")
    @commands.guild_only()
    async def autoreaction(self, ctx: commands.Context):
        """
        View current AutoReactions
        """
        embed = discord.Embed(
            title="Xylo Auto Reactions",
            colour=discord.Colour.green()
        )
        for reaction in self.reactions:
            value = " ".join(reaction.reaction)
            embed.add_field(name=reaction.trigger, value=value, inline=True)

        await ctx.send(embed=embed)

    @commands.group(name="!autoreactions", aliases=["!autoreaction", "!ar"])
    @commands.guild_only()
    @checks.is_mod()
    async def config_autoreactions(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help('!autoreactions')

    @config_autoreactions.command(name="new")
    @commands.guild_only()
    @checks.is_mod()
    async def config_ar_new(self, ctx: Context):
        """
        Setup wizard for a new auto reaction.
        """
        reacts = await self.get_autoreactions(ctx.guild.id)
        name = await ctx.ask("What name will the new auto reaction have?")
        if name is None:
            return await ctx.timeout()
        for r in reacts.reactions:
            if r.name.lower() == name.lower():
                return await ctx.send("There is already a reaction named that in this guild!")
        name = name.replace("$", r"\$")

        ftype = await ctx.ask("What type of filter will this be?\n**1.** Case insensitive and can be found anywhere."
                              "\n**2.** Case sensitive and can be found anywhere."
                              "\n**3.** Case insensitive and it has to only be that text."
                              "\n**4.** Case sensitive and it has to only be that text.")
        if ftype is None:
            return await ctx.timeout()
        try:
            ftype = int(ftype)
        except ValueError:
            return await ctx.send("You need to specify a number from 1-4.")
        if ftype > 4 or ftype < 0:
            return await ctx.send("You need to specify a number from 1-4.")

        filter = await ctx.ask("What should I look for? This can be 40 characters long.")
        if filter is None:
            return await ctx.timeout()
        if len(filter) > 40:
            return await ctx.send("Too long!")
        filter = filter.replace("$", r"\$")

        # TODO Eventually add the ability to add text to this... I have everything in place for it.
        rtype = 0

        data = await ctx.ask("What data should I respond with? If it's reactions it has to be emojis. (Split with spaces)")
        if data is None:
            return await ctx.timeout()
        if rtype == ReactionType.reaction:
            split = data.split(' ')
            emojis = []
            for s in split:
                e = await StandardEmoji().convert(ctx, s)
                if e is not None:
                    emojis.append(e)
                e = await commands.EmojiConverter().convert(ctx, s)
                if e is not None:
                    emojis.append(f"<:{e.name}:{e.id}>")
            data = ' '.join(emojis)

        final = AutoReactionConfig.ReactionData(name, filter, data, ftype=ftype, rtype=rtype)
        embed = await self.get_about_embed(final)
        result = await ctx.prompt("Does this look right?", embed=embed)

    async def get_about_embed(self, data: AutoReactionConfig.ReactionData):
        embed = discord.Embed(
            title=f"AutoReaction: {data.name}",
            colour=discord.Colour.gold()
        )
        message = f"Filter Type: `{str(data.ftype)}` Filter: `{data.filter}`\nResult Type: `{str(data.rtype)}` Result Data: `{data.data}`"
        embed.description = message
        return embed

    @commands.command(name="emoji")
    async def emoji(self, ctx: Context, emoji_found: commands.Greedy[typing.Union[discord.Emoji, StandardEmoji]] = None):
        if emoji_found is None:
            return await ctx.send("No emoji in that text!")

        message = "Emoji's found:"
        for emoji in emoji_found:
            if emoji is not None:
                if isinstance(emoji, discord.Emoji):
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
