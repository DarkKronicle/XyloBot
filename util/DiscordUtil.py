import discord
from storage.Config import *
import io
import aiohttp
from discord.ext import commands
from storage.Database import *


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


def get_db_role(guild: discord.Guild, role):
    db = Database()
    settings: dict = db.get_settings(str(guild.id))
    if "roles" in settings and role in settings["roles"]:
        return guild.get_role(settings["roles"][role])
    return None


def get_db_channel(guild: discord.Guild, channel):
    db = Database()
    settings: dict = db.get_settings(str(guild.id))
    if "channels" in settings and channel in settings["channels"]:
        return guild.get_channel(settings["channels"][channel])
    return None


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


def check_verification(guild: discord.Guild, settings):
    if "channels" in settings and "setup" in settings["channels"] and "setup-logs" in settings["channels"]:
        if guild.get_channel(int(settings["channels"]["setup"])) is None or guild.get_channel(
                int(settings["channels"]["setup-logs"])) is None:
            return False
    else:
        return False
    if "roles" in settings and "verifier" in settings["roles"] and "unverified" in settings["roles"]:
        if guild.get_role(int(settings["roles"]["verifier"])) is None or guild.get_role(
                int(settings["roles"]["unverified"])) is None:
            return False
    else:
        return False

    return True


def set_check_verification(guild: discord.Guild):
    db = Database()
    settings: dict = db.get_settings(str(guild.id))
    return check_verification(guild, settings)


def is_allowed():
    permission = commands.has_permissions(administrator=True).predicate

    async def predicate(context: commands.Context):
        # if await context.bot.is_owner(context.author):
        #     return True
        if await permission(context):
            return True
        role = get_db_role(context.guild, "botmanager")
        if role is not None:
            comm = commands.has_role(int(role)).predicate
            return await comm(context)
        return False

    return commands.check(predicate)


def is_verifier():
    permission = commands.has_permissions(administrator=True).predicate

    async def predicate(context: commands.Context):
        if await permission(context):
            return True
        role = get_db_role(context.guild, "verifier")
        if role is not None:
            comm = commands.has_role(int(role)).predicate
            return await comm(context)
        return False

    return commands.check(predicate)
