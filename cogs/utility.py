import discord
from storage import cache
from storage.database import Database
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
    async def invite(self, ctx: commands.Context):
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


def setup(bot):
    bot.add_cog(Utility())