from storage.Database import *
import discord

setup_channels = {}

verifier_roles = {}

unverified_roles = {}

verify_enabled = {}

fields = {}

fun = {}


def clear_setup_cache(guild):
    if guild in setup_channels:
        setup_channels.pop(guild.id)


def get_setup_channel(guild: discord.Guild):
    if guild.id in setup_channels:
        return setup_channels[guild.id]
    else:
        db = Database()
        settings = db.get_settings(str(guild.id))
        if "channels" in settings and "setup" in settings["channels"]:
            channel = guild.get_channel(int(settings["channels"]["setup"]))
            setup_channels[guild.id] = channel
            return channel
        else:
            return None


def clear_unverified_cache(guild):
    if guild in unverified_roles:
        unverified_roles.pop(guild.id)


def get_unverified_role(guild: discord.Guild):
    if guild.id in unverified_roles:
        return unverified_roles[guild.id]
    else:
        db = Database()
        settings = db.get_settings(str(guild.id))
        if "roles" in settings and "unverified" in settings["roles"]:
            role = guild.get_role(int(settings["roles"]["unverified"]))
            unverified_roles[guild.id] = role
            return role
        else:
            return None


def clear_enabled_cache(guild):
    if guild in verify_enabled:
        verify_enabled.pop(guild.id)


def get_enabled(guild: discord.Guild):
    if guild.id in verify_enabled:
        return verify_enabled[guild.id]
    else:
        db = Database()
        settings = db.get_settings(str(guild.id))
        if "verification" in settings and "enabled" in settings["verification"]:
            channel = settings["verification"]["enabled"]
            verify_enabled[guild.id] = channel
            return channel
        else:
            return None


def clear_fields_cache(guild):
    if guild in verify_enabled:
        verify_enabled.pop(guild.id)


def get_fields(guild: discord.Guild):
    if guild.id in fields:
        return fields[guild.id]
    else:
        db = Database()
        settings = db.get_settings(str(guild.id))
        if "verification" in settings and "fields" in settings["verification"]:
            field = settings["verification"]["fields"]
            fields[guild.id] = field
            return field
        else:
            return None


def clear_fun_cache(guild):
    if guild in fun:
        fun.pop(guild.id)


def get_fun(guild: discord.Guild):
    if guild.id in fun:
        return fun[guild.id]
    else:
        db = Database()
        settings = db.get_settings(str(guild.id))
        if "fun" in settings:
            fun_field = settings["fun"]
            fun[guild.id] = fun_field
            return fun_field
        else:
            return None
