from Config import *
import random
from Storage import *
from DiscordUtil import *
from discord.ext.commands import Bot
from discord.ext import commands


class Setup(commands.Cog):
    bot: commands.Bot
    bot = Bot

    # Dictionaries for keeping track of who is being verified.

    step = {}
    names = {}
    schools = {}
    to_verify = []

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        # Checks to see if in #setup
        if message.channel.name == "setup":
            author = message.author
            # Gets what step of the setting up process they're in
            if author in self.step:
                current_step = self.step[author]
            else:
                current_step = 1

            if await get_role_name("unverified", author.guild) not in author.roles:
                return
            else:
                # Only other people who have access is staff, so don't do anything if it isn't an 'unverified' person
                await message.delete()

            if current_step is 1:
                embed = discord.Embed(
                    title="1: Setup",
                    description='I need to know your first name.',
                    colour=discord.Colour.blurple()
                )
                embed.add_field(name="Usage:", value="NAME", inline=True)

                self.step[author] = 2
                await message.channel.send(embed=embed, delete_after=15)

            elif current_step is 2:
                name: str = message.content
                self.names[author] = name
                embed = discord.Embed(
                    title="2: Hello " + name + "!",
                    description="Now I need your school, use initials. (i.e. RHS, or none)",
                    colour=discord.Colour.blurple()
                )
                embed.add_field(name="Usage:", value="SCHOOL", inline=True)
                self.step[author] = 3
                await message.channel.send(embed=embed, delete_after=15)

            elif current_step is 3:
                school = message.content
                self.schools[author] = school
                embed = discord.Embed(
                    title="3: " + school + ". Nice!",
                    description="That's all you need to do for now, thanks! A staff member will verify you shortly.",
                    colour=discord.Colour.blurple()
                )
                self.step[author] = 4
                self.to_verify.append(author)
                await message.channel.send(embed=embed, delete_after=15)
                # Notify staff that the person is done
                who = ":bell: `" + author.name + "` just went through the verification process!\n Name: `" + self.names[
                    author] + "` School: `" + self.schools[author] + "`"
                channel_name = await get_channel_name("setup-verify", message.guild)
                await channel_name.send(who)

            elif current_step is 4:
                # Send this anytime they try to go further.
                embed = discord.Embed(
                    title="4: You're all done!",
                    description="A staff member will verify you before you can continue.",
                    colour=discord.Colour.blurple()
                )
                await message.channel.send(embed=embed, delete_after=15)

    async def verify_user(self, user: discord.Member, guild):
        """
        Verifies user
        """

        print("Verifying " + user.name)
        storage = Storage()
        # Log to database
        storage.insert_user_data(str(user.id), self.names[user], self.schools[user])

        # Get random welcome message
        welcome = await get_channel_name("welcome", guild)
        join = Config(file="files/join.json")
        messages = join.data["messages"]
        message = random.choice(messages)
        message = message.replace("{user}", user.mention)
        # Get random role
        # randrole = join.data["roles"]
        # Setup weights for roles
        # weighted = []
        # for rol in randrole:
        #     weight = randrole[rol]
        #     weighted = weighted + [rol] * weight

        # Get roles to be assigned...
        # role = await getrolename(random.choice(weighted), guild)
        # role = await getrolename("Common Folk", guild)
        # role2 = await getrolename("gamer", guild)
        role3 = await get_role_name("lifer", guild)
        role4 = await get_role_name("spam", guild)

        # Channels to be mentioned in welcome message
        rules = await get_channel_name("helpful-commands", guild)
        helpful = await get_channel_name("rules", guild)

        # Assign user roles and nick
        await user.edit(roles=[role3, role4], nick=self.names[user])
        # Remove past data...
        self.to_verify.remove(user)
        del self.names[user]
        del self.schools[user]
        del self.step[user]
        await welcome.send(
            message + " Make sure you read " + rules.mention + " and check out "
            + helpful.mention) #+ ". You've been assigned the random role of... *" + role.name + "*")



    async def reject_user(self, user: discord.Member, message):
        """
        Rejects user
        """

        print("Rejecting " + user.name)
        # Remove data
        self.to_verify.remove(user)
        del self.names[user]
        del self.schools[user]
        del self.step[user]

        # Check for dm channel
        if user.dm_channel is None:
            await user.create_dm()
        dm = user.dm_channel
        # Send message. If there is an extra staff message that will be added.
        if message is None:
            await dm.send(
                "Your verification has been declined in *Rivertron*. Please contact a staff member if you believe "
                "this is a problem.")
        else:
            await dm.send(
                "Your verification has been declined in *Rivertron*. Please contact a staff member if you believe "
                "this is a problem. \n\nStaff Message: " + str(message))



    @commands.command(name="verify")
    async def verify(self, ctx, *args):
        # Only works in one channel
        if ctx.message.channel.name != "setup-verify":
            return

        # Has to have correct role
        if await get_role_name("Verifier", ctx.guild) not in ctx.message.author.roles:
            return

        if len(args) <= 0 or args[0] == "help":
            # Send help message
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
            embed.add_field(name="`>verify reject <num> [<message>]`",
                            value='Rejects a person based off of their number'
                                  'to them.', inline=False)
            embed.add_field(name="`>verify update <name/school> <id> [value]`",
                            value='Updates database information.', inline=False)
            await ctx.send(embed=embed)

        elif args[0] == "list":
            # Lists current users waiting to be verified and gives a number to each.
            if len(self.to_verify) <= 0:
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
            for user in self.to_verify:
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

            if int(args[1]) <= 0 or int(args[1]) > len(self.to_verify):
                await ctx.send(embed=error, delete_after=15)
                return

            # Gets user to verify based off of number
            user = self.to_verify[int(args[1]) - 1]

            if user is None:
                await ctx.send(embed=error, delete_after=15)
                return

            # Verify user and send message
            await self.verify_user(user, ctx.guild)
            await ctx.send(":bell: `" + ctx.message.author.name + "` has verified`" + user.name + "`!")

        elif args[0] == "reject":

            error = discord.Embed(
                title="Error in Command",
                description="Make sure you only specify 2 arguments. Could be an invalid number. Check list.",
                colour=discord.Colour.red()
            )
            error.add_field(name="Usage:", value="`>verify reject <num>`")

            if len(args) <= 1:
                await ctx.send(embed=error, delete_after=15)
                return

            if int(args[1]) <= 0 or int(args[1]) > len(self.to_verify):
                await ctx.send(embed=error, delete_after=15)
                return

            user = self.to_verify[int(args[1]) - 1]

            if user is None:
                await ctx.send(embed=error, delete_after=15)
                return

            # Reject and send message
            if ' '.join(args[2:]) is not None:
                await self.reject_user(user, ' '.join(args[2:]))
            else:
                await self.reject_user(user)

            await ctx.send(":bell: `" + ctx.message.author.name + "` has rejected `" + user.name + "`!")

        elif args[0] == "update":
            error = discord.Embed(
                title="Error in Command",
                description="Make sure you only specify 2 arguments. Could be an invalid number. Check list.",
                colour=discord.Colour.red()
            )
            error.add_field(name="Usage:", value="`>verify update <id> <name> <school>`")

            if len(args) <= 3:
                await ctx.send(embed=error, delete_after=15)
                return

            user = await get_user_id(args[2], ctx.guild)
            if user is None:
                await ctx.send(embed=error, delete_after=15)
                return

            if args[1] == "name":
                storage = Storage()
                # Log to database
                storage.change_user_name(str(user), ' '.join(args[3:]))
                await ctx.send(f"Success! {user} name has been changed!")
                return
            elif args[1] == "school":
                storage = Storage()
                # Log to database
                storage.change_user_school(str(user), ' '.join(args[3:]))
                await ctx.send(f"Success! {user} school has been changed")
                return
            else:
                await ctx.send(embed=error, delete_after=15)
                return



def setup(bot):
    bot.add_cog(Setup(bot=bot))
