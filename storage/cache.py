from storage.database import *
import discord


prefixes = {}


def clear_prefix_cache(guild):
    if guild.id in prefixes:
        prefixes.pop(guild.id)


def get_prefix(guild: discord.Guild):
    if guild.id in prefixes:
        return prefixes[guild.id]
    else:
        db = Database()
        prefix = db.get_prefix(str(guild.id))
        prefixes[guild.id] = prefix
        return prefix
