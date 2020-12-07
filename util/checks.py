from discord.ext import commands
from discord.enums import Enum


class ExtraBucketType(Enum):

    user_guild = 0

    def get_key(self, msg):
        if self is ExtraBucketType.user_guild:
            if msg.guild is None:
                return msg.author.id
            else:
                return (msg.author.id, msg.guild.id)


class ExtraCooldown:

    def __init__(self, rate, per, bucket: ExtraBucketType):
        self.default_mapping = commands.CooldownMapping.from_cooldown(rate, per, commands.BucketType.default)
        self.default_mapping._cooldown.type = bucket

    def __call__(self, ctx: commands.Context):
        bucket = self.default_mapping.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True


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
