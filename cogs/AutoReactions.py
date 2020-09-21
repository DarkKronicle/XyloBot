from discord.ext import commands
import discord
from storage.Config import ConfigData


class AutoReaction:

    def __init__(self, trigger: str, reaction: list, aliases: list, case: bool):
        self.trigger = trigger
        self.reaction = reaction
        self.aliases = aliases
        self.case = case


class AutoReactions(commands.Cog):

    autoreactions = ConfigData.autoreactions
    reactions = []
    config_reactions = autoreactions.data["reactions"]

    for react in config_reactions:
        data = config_reactions[react]
        reactions.append(AutoReaction(react, data["emojis"], data["aliases"], data["case"]))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

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
