import discord
from discord.ext import commands

from xylo_bot import XyloBot


class Logging(commands.Cog):

    def __init__(self, bot):
        self.bot: XyloBot = bot

    async def get_guild_embed(self, guild: discord.Guild, *, embed=discord.Embed(title="Guild Information",
                                                                                 colour=discord.Colour.purple())):
        embed.add_field(name="Name/ID", value=f"{guild.name} (ID: `{guild.id}`")
        embed.add_field(name="Owner", value=f"{guild.owner} (ID: `{guild.owner.id}`")
        total = guild.member_count
        bots = sum(m.bot for m in guild.members)
        text = 0
        voice = 0
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                text = text + 1
            elif isinstance(channel, discord.VoiceChannel):
                voice = voice + 1
        message = f"Text Channels: `{text}`\nVoice Channels: `{voice}`\nTotal Channels: `{text + voice}`\n\nMembers: `{total}`\nBots: `{bots}`"
        embed.description = message
        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)

        if guild.me:
            embed.timestamp = guild.me.joined_at

        return embed

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = await self.get_guild_embed(guild, embed=discord.Embed(title="New Guild!", colour=discord.Colour.green()))
        await self.bot.log.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        embed = await self.get_guild_embed(guild, embed=discord.Embed(title="Left Guild", colour=discord.Colour.red()))
        await self.bot.log.send(embed=embed)


def setup(bot):
    bot.add_cog(Logging(bot))
