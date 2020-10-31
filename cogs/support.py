from datetime import datetime

import discord
from discord.ext import commands

from util.context import Context


class Support(commands.Cog):
    """
    Get support from the bot using PM's and request features.

    These are rate limited and you can be banned by spamming this.
    """

    @commands.command(name="suggest", aliases=["feedback", "helpme"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def suggest(self, ctx: Context, *, feedback: str = None):
        """
        Gives feedback and suggestions about the bot. You can use this to send errors or
        """

        if feedback is None:
            return await ctx.send_help('suggest')

        channel = ctx.bot.get_channel(772138002397790248)
        if channel is None:
            return await ctx.send("Sorry, but suggestions are currently not working.")

        embed = discord.Embed(
            title="New Feedback",
            description=feedback,
            colour=discord.Colour.purple()
        )

        embed.timestamp = datetime.now()
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"Author ID: {ctx.author.id}")

        if ctx.guild is not None:
            embed.add_field(name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})")
            embed.add_field(name="Channel", value=f"{ctx.channel.name} ({ctx.channel.id})")

        await channel.send(embed=embed)
        await ctx.send("Feedback sent! Thanks! You may get a DM from me in the near future.")

    @commands.command(name="pm", aliases=["dm"], hidden=True)
    @commands.is_owner()
    async def pm(self, ctx: Context, *, user_id: int = None, content: str = None):
        """
        PM a user regarding feedback or anything else.
        """
        if user_id is None:
            return await ctx.send("Please specify a correct user ID.")

        if content is None:
            content = await ctx.ask("What do you want to say?")
            if content is None:
                return await ctx.timeout()

        user = ctx.bot.get_user(user_id)
        if user is None:
            return await ctx.send("Can't find this user!")

        dm = await ctx.get_dm(user)
        await dm.send(content + "\n\n*This DM is not monitored. If you need more help join the support server in "
                                "`>about`.*")
        await ctx.send("DM sent!")


def setup(bot):
    bot.add_cog(Support())
