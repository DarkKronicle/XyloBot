from discord.ext import commands
import discord
import enum
from storage.Config import ConfigData
from util.DiscordUtil import *


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
                file = get_file_from_image(f, f)
                if file is not None:
                    file_list.append(file)
        if len(file_list) > 0:
            await message.channel.send(message=self.text, files=file_list)
        else:
            await message.channel.send(self.text)


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
        texts.append(AutoText(text, data["text"], data["aliases"], data["case"], data["type"], data["files"]))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Don't want recursion now... it's the skeletons all over
        if message.author.bot:
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
                if content[0] == self.bot.command_prefix:
                    if content[1:] == text.trigger or content in text.aliases:
                        await text.send(message)
                        continue
            elif text.texttype == TextType.only:
                if content == text.trigger or content in text.aliases:
                    await text.send(message)
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
                            await text.send(message)
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
