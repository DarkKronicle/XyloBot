from discord.ext import commands
import discord
from util.context import Context
from storage.database import Database


class UserSettings(commands.Cog):
    """
    Settings that users can customize.
    """
    socials = [
        "twitch",
        "youtube"
    ]

    # @commands.group(name="social", invoke_without_command=True, usage="<twitch|youtube>")
    # async def social(self, ctx: Context, *args):
    #     """
    #     Social information that is global.
    #     """
    #     if ctx.invoked_subcommand is None and len(args) <= 1:
    #         embed = discord.Embed(title="Socials", description="You may use `twitch` `youtube`")
    #         embed.add_field(name="Usage", value="`social <social...> <url>`")
    #         await ctx.send(embed=embed)
    #         return
    #
    #     if len(args) > 1:
    #         social = args[0]
    #         if social not in self.socials:
    #             embed = discord.Embed(title="Socials", description="You may use `twitch` `youtube`")
    #             embed.add_field(name="Usage", value="`social <social...> <url>`")
    #             await ctx.send(embed=embed)
    #             return
    #         db = Database()
    #         data = db.get_user_social(str(ctx.author.id))
    #         if data is None:
    #             data = {}
    #         data[social] = args[1]
    #         author: discord.Member = ctx.author
    #         role = cache.get_content_role(ctx.guild)
    #         create = False
    #         if role is not None and role in ctx.author.roles:
    #             await author.remove_roles(role)
    #             create = True
    #         db.set_user_social(str(author.id), data)
    #         if create:
    #             await ctx.send("Social set! You will have to get the content creator role again.")
    #             return
    #         else:
    #             await ctx.send("Social set! You can have a staff member verify you to get notifications sent to a "
    #                            "channel.")
    #             return
    #
    # @social.group(name="who", usage="<user>")
    # async def who(self, ctx, member: discord.Member):
    #     if member is None:
    #         await ctx.send("You need to specify a correct user.")
    #         return
    #     db = Database()
    #     data = db.get_user_social(str(member.id))
    #     if data is None:
    #         await ctx.send("This user has not set any social data on them.")
    #         return
    #     message = f"Socials for {member.display_name}:\n"
    #     for d in data:
    #         message = message + f"{d}: {data[d]}"
    #     await ctx.send(embed=discord.Embed(title=f"Socials for {member.display_name}", description=message))
    #     return

def setup(bot):
    bot.add_cog(UserSettings())
