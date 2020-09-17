import discord

async def get_role_name(role: str, guild: discord.Guild):
    """
    Get role from name
    """
    for name in guild.roles:
        if name.name == role:
            return name

    return None


async def get_channel_name(channel: str, guild: discord.Guild):
    """
    Get channel from name
    """
    for name in guild.text_channels:
        if name.name == channel:
            return name

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