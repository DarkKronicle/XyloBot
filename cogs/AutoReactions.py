from discord.ext import commands
import discord
from Config import *


class AutoReaction:

    def __init__(self, trigger: str, reaction: list):
        self.trigger = trigger
        self.reaction = reaction


class AutoReactions(commands.Cog):

    join = Config(file="files/autoreaction.json")
    reactions = []
    config_reactions = join.data["reactions"]

    for react in config_reactions:
        reactions.append(AutoReaction(react, config_reactions[react]))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        content: str = message.content.lower()

        for reaction in self.reactions:
            if reaction.trigger in content:
                for emoji in reaction.reaction:
                    await message.add_reaction(emoji)

        # if "xylo" in content:
        #     await message.add_reaction('👻')
        #
        # if "!poll!" in content:
        #     await message.add_reaction('✔️')
        #     await message.add_reaction('❌')


def setup(bot):
    bot.add_cog(AutoReactions(bot))
