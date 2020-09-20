from discord.ext import commands
import discord
from storage.JSONReader import *
from storage.Config import ConfigData


class AutoReaction:

    def __init__(self, trigger: str, reaction: list):
        self.trigger = trigger
        self.reaction = reaction


class AutoReactions(commands.Cog):

    autoreactions = ConfigData.autoreactions
    reactions = []
    config_reactions = autoreactions.data["reactions"]

    for react in config_reactions:
        reactions.append(AutoReaction(react, config_reactions[react]))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        content: str = message.content.lower()

        for reaction in self.reactions:
            if reaction.trigger in content:
                for emoji in reaction.reaction:
                    await message.add_reaction(emoji)

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
