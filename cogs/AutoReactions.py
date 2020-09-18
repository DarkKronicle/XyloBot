from discord.ext import commands
import discord


class AutoReactions(commands.Cog):

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        content: str = message.content.lower()

        if "xylo" in content:
            await message.add_reaction('👻')

        if "!poll!" in content:
            await message.add_reaction('✔️')
            await message.add_reaction('❌')


def setup(bot):
    bot.add_cog(AutoReactions(bot))
