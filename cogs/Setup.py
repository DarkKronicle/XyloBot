import discord
from discord.ext.commands import Bot
from discord.ext import commands
from Config import *
import random

class Setup(commands.Cog):
    bot = Bot

    step = {}
    names = {}
    schools = {}
    toverify = []

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.name == "setup":
            author = message.author
            await message.delete()
            if author in self.step:
                curstep = self.step[author]

            else:
                curstep = 1

            if curstep is 1:
                embed = discord.Embed(
                    title="1: Setup",
                    description='I need to know your first name.',
                    colour=discord.Colour.blurple()
                )
                embed.add_field(name="Usage:", value="NAME", inline=True)

                self.step[author] = 2
                await message.channel.send(embed=embed, delete_after=15)

            elif curstep is 2:
                name = message.content
                self.names[author] = name
                embed = discord.Embed(
                    title="2: Hello " + name + "!",
                    description="Now I need your school, use initals. (i.e. RHS, or none)",
                    colour=discord.Colour.blurple()
                )
                embed.add_field(name="Usage:", value="SCHOOL", inline=True)
                self.step[author] = 3
                await message.channel.send(embed=embed, delete_after=15)

            elif curstep is 3:
                school = message.content
                self.schools[author] = school
                embed = discord.Embed(
                    title="3: " + school + ". Nice!",
                    description="That's all you need to do for now, thanks! A staff member will verify you shortly.",
                    colour=discord.Colour.blurple()
                )
                self.step[author] = 4
                self.toverify.append(author)
                await message.channel.send(embed=embed, delete_after=15)
                who = ":bell: `" + author.name + "` just went through the verification process!\n Name: `" + self.names[
                    author] + "` School: `" + self.schools[author] + "`"
                channelname = await self.getChannelName("setup-verify", message.guild)
                await channelname.send(who)

            elif curstep is 4:
                embed = discord.Embed(
                    title="4: You're all done!",
                    description="A staff member will verify you before you can continue.",
                    colour=discord.Colour.blurple()
                )
                await message.channel.send(embed=embed, delete_after=15)

    async def getRoleName(self, role, guild):
        """

        :type guild: Guild
        :type role: str
        """
        for name in guild.roles:
            if name.name == role:
                return name

        return None

    async def getChannelName(self, channel, guild):
        """

        :type guild: Guild
        :type role: str
        """
        for name in guild.text_channels:
            if name.name == channel:
                return name

        return None


    async def verifyUser(self, user, guild):
        print("Verifying " + user.name)
        config = Config(file="files/verified.json")
        config.data[str(user.id)] = {"name": self.names[user], "school": self.schools[user]}
        config.savefile()
        welcome = await self.getChannelName("welcome", guild)
        join = Config(file="files/join.json")
        messages = join.data["messages"]
        message = random.choice(messages)
        message = message.replace("{user}", user.mention)
        randrole = join.data["roles"]
        weighted = []
        for rol in randrole:
            weight = randrole[rol]
            weighted = weighted + [rol] * weight

        role = await self.getRoleName(random.choice(weighted), guild)

        rules = await self.getChannelName("helpful-commands", guild)
        helpful = await self.getChannelName("rules", guild)

        await user.edit(roles=[role],nick=self.names[user])
        self.toverify.remove(user)
        del self.names[user]
        del self.schools[user]
        del self.step[user]
        await welcome.send(message + " Make sure you read "+rules.mention+" and check out "+helpful.mention+". You've been assigned the random role of... *" + role.name+"*")


    async def rejectUser(self, user):
        print("Rejecting " + user.name)
        self.toverify.remove(user)
        del self.names[user]
        del self.schools[user]
        del self.step[user]
        if user.dm_channel is None:
            await user.create_dm()
        dm = user.dm_channel
        await dm.send("Your verification has been declined in *Rivertron*. Please contact a staff member if you believe this is a problem. You have one more attempt.")


    @commands.command(name="verify")
    async def verify(self, ctx, *args):
        if ctx.message.channel.name != "setup-verify":
            return

        if await self.getRoleName("Verifier", ctx.guild) not in ctx.message.author.roles:
            return

        if len(args) <= 0:
            embed = discord.Embed(
                title="Verify Help",
                description="All Commands for `>verify`",
                colour=discord.Colour.blue()
            )
            embed.add_field(name="`>verify list`", value='Gets all people that need to be verified and assigns a '
                                                         'number '
                                                         'to them.', inline=False)
            embed.add_field(name="`>verify accept <num>`", value='Verifies a person based off of their number.'
                            , inline=False)
            embed.add_field(name="`>verify reject <num>`", value='Rejects a person based off of their number'
                                                                 'to them.', inline=False)
            await ctx.send(embed=embed)
        elif args[0] == "list":
            if len(self.toverify) <= 0:
                embed = discord.Embed(
                    title="To Verify:",
                    description="No one!",
                    colour=discord.Colour.green()
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="To Verify:",
                description="All users who still need to be verified.",
                colour=discord.Colour.blue()
            )
            i = 0
            for user in self.toverify:
                i = i + 1
                embed.add_field(name=str(i) + ".", value=user.name)

            await ctx.send(embed=embed)

        elif args[0] == "accept":
            error = discord.Embed(
                title="Error in Command",
                description="Make sure you only specify 2 arguments.",
                colour=discord.Colour.red()
            )
            error.add_field(name="Usage:", value="`>verify accept <num>`")
            if len(args) <= 1 or len(args) >= 3:
                await ctx.send(embed=error, delete_after=15)
                return

            if int(args[1]) <= 0 or int(args[1]) > len(self.toverify):
                await ctx.send(embed=error, delete_after=15)
                return

            user = self.toverify[int(args[1])-1]

            if user is None:
                await ctx.send(embed=error, delete_after=15)
                return

            await self.verifyUser(user, ctx.guild)
            await ctx.send(":bell: Verifying " + user.name + "!")

        elif args[0] == "reject":
            error = discord.Embed(
                title="Error in Command",
                description="Make sure you only specify 2 arguments. Could be an invalid number. Check list.",
                colour=discord.Colour.red()
            )
            error.add_field(name="Usage:", value="`>verify reject <num>")
            if len(args) <= 1 or len(args) >= 3:
                await ctx.send(embed=error, delete_after=15)
                return

            if int(args[1]) <= 0 or int(args[1]) > len(self.toverify):
                await ctx.send(embed=error, delete_after=15)
                return

            user = self.toverify[int(args[1])-1]

            if user is None:
                await ctx.send(embed=error, delete_after=15)
                return

            await self.rejectUser(user)
            await ctx.send(":bell: Rejecting " + user.name + "!")




def setup(bot):
    bot.add_cog(Setup(bot=bot))
