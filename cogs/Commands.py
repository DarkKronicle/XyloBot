import discord
from discord.ext import commands


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send("Pong!")

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     try:
    #         await ctx.message.delete()
    #     finally:
    #         print("An error occurred in " + ctx.message.content)
    #     embed = discord.Embed(
    #         title="Error in command - " + str(type(error)),
    #         description="There was an error in your command, please double check that it was formatted correctly and "
    #                     "if it persists, contact the developer.",
    #         colour=discord.Colour.red()
    #     )
    #     args = ''
    #     embed.add_field(name="Command Used:", value=ctx.message.content)
    #     embed.set_footer(text="Default error message. Deletes after 30 seconds.")
    #     await ctx.send(embed=embed, delete_after=30)


def setup(bot):
    bot.add_cog(Commands(bot))
