from discord.ext import commands


def user_guild(msg):
    if msg.guild is None:
        return msg.author.id
    else:
        return msg.author.id, msg.guild.id


class AdvancedCooldown:
    """
    The base class for cooldowns are really cool, so I wanted to implement something similar. The problem is
    there is only 7 types of cooldowns. I created this class to open that.
    """

    def __init__(self, rate, per, bucket):
        self.default_mapping = commands.CooldownMapping(commands.Cooldown(rate, per, bucket))

    def __call__(self, ctx: commands.Context):
        bucket = self.default_mapping.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True


class WhitelistCooldown:

    def __init__(self, rate, per, other_rate, other_per, whitelist_type, type, whitelisted):
        self.rate = rate
        self.per = per
        self.other_rate = other_rate
        self.other_per = other_per
        self.whitelist_type = whitelist_type
        self.type = type
        self.whitelisted = whitelisted
        self.cool = AdvancedCooldown(rate, per, type)
        self.white = AdvancedCooldown(other_rate, other_per, whitelist_type)

    def __call__(self, ctx):
        key = self.whitelist_type.get_key(ctx.message)
        if key in self.whitelisted:
            return self.white(ctx)
        else:
            return self.cool(ctx)


def cooldown(rate, per, type):
    cool = AdvancedCooldown(rate, per, type)

    def predicate(ctx):
        return cool(ctx)

    return commands.check(predicate)


def whitelist_cooldown(rate, per, other_rate, other_per, whitelist_type, type, whitelisted):
    """
    Advanced Whitelist double cooldown weird thing
    :param rate: The default rate
    :param per: Default per
    :param other_rate: Whitelisted rate
    :param other_per: Whitelisted per
    :param whitelist_type: BucketType for what keys should be in whitelisted
    :param type: Normal BucketType
    :param whitelisted: list for what values are whitelisted
    :return:
    """
    cool = WhitelistCooldown(rate, per, other_rate, other_per, whitelist_type, type, whitelisted)

    def predicate(ctx):
        return cool(ctx)

    return commands.check(predicate)


# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/checks.py#L11
# MPL-2.0
async def check_permissions(ctx, perms, *, check=all, channel=None):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if channel is None:
        channel = ctx.channel
    resolved = channel.permissions_for(ctx.author)
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


async def check_guild_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return True

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def is_admin():
    async def predicate(ctx):
        return await check_guild_permissions(ctx, {'administrator': True})

    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        return await check_guild_permissions(ctx, {'manage_server': True, 'administrator': True}, check=any)

    return commands.check(predicate)


def guild(*args):
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        return ctx.guild.id in args

    return commands.check(predicate)


def owner_or(*args):
    async def predicate(ctx):
        if ctx.author.id in args:
            return True
        return await ctx.bot.is_owner(ctx.author)

    return commands.check(predicate)
