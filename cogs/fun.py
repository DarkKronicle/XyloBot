import random

import typing
from discord.ext import commands

import util.emoji_util as emoji
import time
from util import checks
from util.context import Context
from util.discord_util import *
from storage.config import *


class SufferStorage:

    class _Sufferer:
        __slots__ = ("user", "guild", "expire", "emoji_reaction", "start")

        def __init__(self, user, guild, expire, *, start=None, emoji_reaction=None):
            self.user = user
            self.guild = guild
            self.expire = expire
            self.emoji_reaction = emoji_reaction
            self.start = start or time.monotonic()

        def expired(self, *, current=None):
            if current is None:
                current = time.monotonic()
            return current > (self.expire + self.start)

        async def react(self, message):
            if self.emoji_reaction is None:
                e = random.choice(emoji.all_emojis)
            else:
                e = self.emoji_reaction
            try:
                message.add_reaction(e)
            except:
                pass

    def __init__(self):
        self._storage = []

    def add(self, user, guild, *, expire=60*30, emoji=None):
        self._storage.append(self._Sufferer(user, guild, expire, emoji_reaction=emoji))

    def get_suffer(self, user, guild):
        self._check_integrity()
        items = []
        for suffer in self._storage:
            if suffer.user == user and suffer.guild == guild:
                items.append(suffer)
        return items

    def from_message(self, message: discord.Message):
        if message.guild is None:
            return None
        return self.get_suffer(message.author.id, message.guild.id)

    async def react(self, message):
        suffer = self.from_message(message)
        for s in suffer:
            await s.react(message)

    def _check_integrity(self):
        to_remove = []
        current = time.monotonic()
        for i, sufferer in enumerate(self._storage):
            if sufferer.expired(current=current):
                to_remove.append(sufferer)
        for i in to_remove:
            del self._storage[i]


class Fun(commands.Cog, name="Fun"):
    """
    Fun commands for Xylo. These each may be disabled by staff.
    """

    def __init__(self, bot):
        self.bot = bot
        self.suffer = SufferStorage()

    @commands.group(name="lober", invoke_without_command=True)
    async def lober(self, ctx: commands.Context):
        """
        Lober command.
        """
        await ctx.send_help('lober')

    @lober.command(name="fact")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def fact(self, ctx: commands.Context):
        """
        Sends a lober fact
        """
        rand = random.choice(ConfigData.lober.data["facts"])
        embed = discord.Embed(
            title="**LOBER FACT**",
            description=rand,
            colour=discord.Colour.dark_gray()
        )
        await ctx.send(embed=embed)

    @lober.command(name="image")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image(self, ctx: commands.Context):
        """
        Sends a lober image.
        """
        lobers = await get_file_from_image(
            "https://media.discordapp.net/attachments/757781442674688041/759604260110598144/i64khd2lbns41.png?width=693&height=687",
            "lober.png")
        await ctx.send(content="**LOBER MOMENT**", file=lobers)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Don't want recursion now... it's the skeletons all over
        if message.author.bot:
            return

        # Guild only so we don't get into weird configurations.
        if message.guild is None:
            return

        if message.channel.id == 784639082063593503:
            emojis = await emoji.random_reaction(message)
            self.bot.random_stats["baby"] += 1
            if emojis == "👼🏿":
                await message.channel.send(
                    rf"WE HAVE FOUND A BABY! CONGRATZ {message.author.mention}! Amount of babies trying to be found has been {self.bot.random_stats['baby']} times.")
                await message.author.add_roles(message.guild.get_role(784847571473924097))
        else:
            await self.suffer.react(message)

    @commands.command(name="emojistats", hidden=True)
    async def emoji_stats(self, ctx: Context):
        await ctx.send(embed=discord.Embed(
            title="Emoji Stats",
            description=f"Chance to get baby? `1/{len(emoji.all_emojis)}`. Amount of baby checks: `{self.bot.random_stats['baby']}`"
        ))

    @commands.command(name="suffer")
    @commands.guild_only()
    @checks.whitelist_cooldown(1, 60*60*2, 1, 60*15, commands.BucketType.user, checks.ExtraBucketType.user_guild, [332994937450921986])
    async def suffer_person(self, ctx: Context, emoji_react: typing.Union[emoji.StandardEmoji, discord.Emoji, None] = None, *, member: discord.Member = None):
        """
        Make someone in your guild suffer
        """
        if isinstance(emoji, discord.Emoji):
            if emoji_react.guild.id not in (ctx.guild.id, 658371169728331788):
                # We don't want cross guild stuff... but Xylo's server is fine.
                return await ctx.send("Emoji in another server!")
        if member is None:
            return await ctx.send("Please specify a proper user!")
        mid = member.id
        human = member.mention

        minutes = random.randint(15, 45)

        self.suffer.add(mid, ctx.guild.id, expire=minutes*60, emoji=emoji_react)
        await ctx.send(embed=discord.Embed(description=f"Now suffering {human} for the next {minutes} minutes. Enjoy :)",
                                           colour=discord.Colour.green()))


def setup(bot):
    bot.add_cog(Fun(bot))
