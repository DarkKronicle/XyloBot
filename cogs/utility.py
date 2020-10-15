import discord
from storage import cache
from storage.database import Database
from util.context import Context
from util.discord_util import *
from discord.ext import commands
from datetime import datetime, timedelta
from pytz import timezone


def get_time():
    zone = timezone('US/Mountain')
    utc = timezone('UTC')
    now = utc.localize(datetime.now())
    curtime = now.astimezone(zone)
    return curtime


class Utility(commands.Cog):
    """
    Commands to make life easier.
    """
    
    @commands.command(name="invite")
    @commands.guild_only()
    @commands.cooldown(1, 600, commands.BucketType.member)
    async def invite(self, ctx: Context):
        """
        Creates an invite to the server using specific staff settings.
        """
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if "utility" in settings and "invite" in settings["utility"]:
            if settings["utility"]["invite"]["enabled"]:
                channel: discord.TextChannel = ctx.guild.get_channel(settings["utility"]["invite"]["channel"])
                if channel is None:
                    await ctx.send("Error creating invite. Invite channel not found!")
                    return
                
                invite = await channel.create_invite(max_age=1800)
                if invite is None:
                    await ctx.send("Error creating invite. It just didn't create!")
                    return
                
                else:
                    await ctx.send(f"Here's your invite link!\n\n{str(invite)}")
                    log = cache.get_log_channel(ctx.guild)
                    if log is not None:
                        embed = discord.Embed(
                            title=f"New Invite Created {str(ctx.author)}: {str(invite)}",
                            description="",
                            timestamp=get_time()
                        )
                        await log.send(embed=embed)
                        # embed.set_footer(text=f"Today at {get_time().strftime('%I:%M $p')}")
                    return

    @commands.command(name="dmme")
    async def dmme(self, ctx: Context):
        dm = await ctx.get_dm()
        await dm.send("Hello there!")

    @commands.command(name="ping")
    async def ping(self, ctx: Context):
        await ctx.send("Pong!")

    @commands.command(name="grade")
    async def grade(self, ctx: Context, *args):
        """
        Calculates your grade based off of categories.

        Format each arg like CURRENT|OUTOF|WEIGHT.
        """
        if len(args) == 0:
            await ctx.send("Make sure to put in grades like this: `grade CURRENT|OUTOF|WEIGHT CURRENT...`")
            return
        if len(args) > 25:
            return await ctx.send("Too many grades ;-;")
        grades = []
        total = []
        for arg in args:
            content = arg.split("|")
            if len(content) != 3:
                return await ctx.send("Argument should be: `CURRENT|OUTOF|WEIGHT`")

            try:
                current = float(content[0])
                outof = float(content[1])
                weight = float(content[2]) / 100
                percent = float(current / outof)
            except ValueError:
                return await ctx.send(
                    f"Could not parse arguments for integers. Args were: `f{content[0]} f{content[1]} f{content[2]}")

            grade = {
                "current": current,
                "outof": outof,
                "weight": weight,
                "percent": percent,
                "weighted": percent * weight
            }
            grades.append(grade)
            total.append(percent * weight)

        totalpercent = 0.0
        for tot in total:
            totalpercent = totalpercent + tot
        embed = discord.Embed(
            colour=discord.Colour.gold()
        )
        message = f"**Normal Grading:** {str(round(totalpercent * 100, 2))}%\n**Standard Based:** {str(round(totalpercent * 4, 2))}\n\n```Percentage | Weighted -=- Current/Total\n"
        for grade in grades:
            message = message + f"\n{str(round(grade['percent'] * 100, 2))}% | {str(round(grade['weighted'] * 100))}% " \
                                f"-=- {str(grade['current'])}/{str(grade['outof'])} "
        message = message + "```"
        embed.description = message
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility())
