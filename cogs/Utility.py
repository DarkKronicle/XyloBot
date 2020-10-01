import discord
from storage import Cache
from storage.Database import Database
from util.DiscordUtil import *
from discord.ext import commands

class Utility(commands.Cog):
    
    @commands.commane(name="invite")
    @commands.cooldown(1, 600, commands.BucketType.member)
    async def invite(self, ctx: commands.Context):
        db = Database()
        settings = db.get_settings(str(ctx.guild.id))
        if "utility" in settings and "invite" in settings["utility"]:
            if settings["utility"]["invite"]["enabled"]:
                channel: discord.TextChannel = ctx.guild.get_channel(settings["utility"]["invite"]["channel"])
                if channel is None:
                    await ctx.send("Error creating invite. Invite channel not found!")
                    return
                
                invite = channel.create_invite(max_age=1800)
                if invite is None:
                    await ctx.send("Error creating invite. It just didn't create!")
                    return
                
                else:
                    await ctx.send(f"Here's your invite link!\n\n{str(invite)}")
                    return


def setup(bot):
    bot.add_cog(Utility())