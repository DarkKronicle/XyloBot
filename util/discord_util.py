import discord
from storage.config import *
import io
import aiohttp
from discord.ext import commands


def get_role(role, guild, bot):
    """
    Get role from name
    """
    guild = get_guild(guild, bot)
    if guild is None:
        return None
    guild: discord.Guild

    if isinstance(role, str):
        role = ConfigData.idstorage.data[str(guild.id)]["roles"][role]
        if role is None:
            return None
        role = guild.get_role(role)
    elif isinstance(role, int):
        role = guild.get_role(role)
        if role is None:
            return None

    role: discord.Role

    return role


def get_guild(guild, bot):
    if isinstance(guild, discord.Guild):
        pass
    elif isinstance(guild, str):
        guild = bot.get_guild(ConfigData.idstorage.data[guild])
        if guild is None:
            return None
    elif isinstance(guild, int):
        guild = bot.get_guild(guild)
        if guild is None:
            return None

    return guild


def get_channel(channel, guild, bot):
    """
    Get role from name
    """
    guild = get_guild(guild, bot)
    if guild is None:
        return None
    guild: discord.Guild

    if isinstance(channel, str):
        channel = ConfigData.idstorage.data[str(guild.id)]["channels"][channel]
        if channel is None:
            return None
        channel = guild.get_channel(channel)
    elif isinstance(channel, int):
        channel = guild.get_channel(channel)
        if channel is None:
            return None

    channel: discord.TextChannel

    return channel


async def get_user_id(discord_id: str, guild: discord.Guild):
    """
    Get user based off of their ID
    """
    try:
        discord_int = int(discord_id)
    except ValueError:
        return None

    return guild.get_member(int(discord_id))


def get_keys(data, *args):
    for arg in args:
        if arg in data:
            data = data[arg]
        else:
            return None
    return data


async def get_file_from_image(url: str, name: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = io.BytesIO(await resp.read())
            return discord.File(data, name)


async def get_data_from_url(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = io.BytesIO(await resp.read())
            return data


def get_member(guild: discord.Guild, member_id):
    for member in guild.members:
        if member.id == member_id:
            return member
    # for member in await guild.fetch_members()
    return None
