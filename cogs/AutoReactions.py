from discord.ext import commands
import discord
import enum
from storage.Config import ConfigData


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

    def __init__(self, trigger: str, text: str, aliases: list, case: bool, texttype: str):
        self.trigger = trigger
        self.text = text
        self.aliases = aliases
        self.case = case
        if texttype is "only":
            self.texttype = TextType.only
        elif texttype is "command":
            self.texttype = TextType.command
        else:
            self.texttype = TextType.anywhere


class AutoReactions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    autoreactions = ConfigData.autoreactions
    reactions = []
    texts = []
    config_reactions = autoreactions.data["reactions"]
    config_text = autoreactions.data["text"]

    for react in config_reactions:
        data = config_reactions[react]
        reactions.append(AutoReaction(react, data["emojis"], data["aliases"], data["case"]))

    for text in config_text:
        data = config_text[text]
        texts.append(AutoText(text, data["text"], data["aliases"], data["case"], data["type"]))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Don't want recursion now... it's the skeletons all over
        if message.author is self.bot:
            return

        # AutoReaction
        for reaction in self.reactions:
            if not reaction.case:
                content: str = message.content.lower()
            else:
                content: str = message.content
            done = False

            if reaction.trigger in content:
                for emoji in reaction.reaction:
                    await message.add_reaction(emoji)
                    done = True
            if not done:
                for alias in reaction.aliases:
                    if done:
                        continue
                    if alias in content:
                        for emoji in reaction.reaction:
                            if done:
                                continue
                            await message.add_reaction(emoji)
                        done = True

        # AutoText
        for text in self.texts:
            if not text.case:
                content: str = message.content.lower()
            else:
                content: str = message.content

            if text.texttype == TextType.command:
                if content[0] is self.bot.command_prefix:
                    if content is text.trigger or content in text.aliases:
                        await message.channel.send(text.text)
                        continue
            elif text.texttype == TextType.only:
                if content is text.trigger or content in text.aliases:
                    await message.channel.send(text.text)
                    continue
            else:
                done = False
                if text.trigger in content:
                    await message.channel.send(text.text)
                    done = True
                if not done:
                    for alias in text.aliases:
                        if done:
                            continue
                        if alias in content:
                            await message.channel.send(text.text)
                            done = True

    @commands.command(name="autoreactions")
    async def autoreaction(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Xylo Auto Reactions",
            colour=discord.Colour.green()
        )
        for reaction in self.reactions:
            value = " ".join(reaction.reaction)
            embed.add_field(name=reaction.trigger, value=value, inline=True)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AutoReactions(bot))
