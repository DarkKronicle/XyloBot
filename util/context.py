"""
This class was heavily based off of https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/cogs/utils/context.py#L23:1
Rapptz is amazing.
The code above was released under MIT license.
"""
import re

import discord
from discord.ext import commands
import asyncio

from storage import db


class CustomCleanContent(commands.Converter):
    """
    Taken and modified from original discord py code to allow for more control over what gets escaped.

    Converts the argument to mention scrubbed version of
    said content.

    This behaves similarly to :attr:`~discord.Message.clean_content`.

    Attributes
    ------------
    fix_channel_mentions: :class:`bool`
        Whether to clean channel mentions.
    use_nicknames: :class:`bool`
        Whether to use nicknames when transforming mentions.
    escape_markdown: :class:`bool`
        Whether to also escape special markdown characters.
    """

    def __init__(self, *, fix_channel_mentions=False, use_nicknames=True, escape_markdown=False, escape_mentions=True, escape_roles=True, escape_everyone=True):
        self.fix_channel_mentions = fix_channel_mentions
        self.use_nicknames = use_nicknames
        self.escape_markdown = escape_markdown
        self.escape_mentions = escape_mentions
        self.escape_roles = escape_roles
        self.escape_everyone = escape_everyone

    async def convert(self, ctx, argument):
        message = ctx.message
        transformations = {}

        if self.fix_channel_mentions and ctx.guild:
            def resolve_channel(id, *, _get=ctx.guild.get_channel):
                ch = _get(id)
                return ('<#%s>' % id), ('#' + ch.name if ch else '#deleted-channel')

            transformations.update(resolve_channel(channel) for channel in message.raw_channel_mentions)

        if self.use_nicknames and ctx.guild:
            def resolve_member(id, *, _get=ctx.guild.get_member):
                m = _get(id)
                return '@' + m.display_name if m else '@deleted-user'
        else:
            def resolve_member(id, *, _get=ctx.bot.get_user):
                m = _get(id)
                return '@' + m.name if m else '@deleted-user'

        if self.escape_mentions:
            transformations.update(
                ('<@%s>' % member_id, resolve_member(member_id))
                for member_id in message.raw_mentions
            )

            transformations.update(
                ('<@!%s>' % member_id, resolve_member(member_id))
                for member_id in message.raw_mentions
            )

        if ctx.guild and self.escape_roles:
            def resolve_role(_id, *, _find=ctx.guild.get_role):
                r = _find(_id)
                return '@' + r.name if r else '@deleted-role'

            transformations.update(
                ('<@&%s>' % role_id, resolve_role(role_id))
                for role_id in message.raw_role_mentions
            )

        def repl(obj):
            return transformations.get(obj.group(0), '')

        pattern = re.compile('|'.join(transformations.keys()))
        result = pattern.sub(repl, argument)

        if self.escape_markdown:
            result = discord.utils.escape_markdown(result)

        # Completely ensure no mentions escape:
        if self.escape_mentions:
            return discord.utils.escape_mentions(result)
        if self.escape_everyone:
            result = result.replace("@here", "@\u200b\\here")
            result = result.replace("@everyone", "@\u200b\\everyone")
        return result


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection = None

    async def timeout(self):
        """
        Sends a timeout message.
        """
        await self.send(f"This has been closed due to a timeout {self.author.mention}.", delete_after=15)

    async def prompt(self, message=None, embed=None, timeout=60, delete_after=True, author_id=None):
        """
        A function to ask a certain user for an answer using yes/no.

        :param message: String for what the question is.
        :param timeout: How long the bot will wait for.
        :param delete_after: Should the message be deleted after?
        :param author_id: Who should respond. If None it will default to context author.
        :return: True if yes, false if no, None if timeout.
        """

        if message is None and embed is None:
            raise ValueError("Message and embed can't be NoneType!")

        message = await self.send(content=message, embed=embed)

        answer = None

        if author_id is None:
            author_id = self.author.id

        def check(msg):
            nonlocal answer
            if msg.author.id != author_id or msg.channel != message.channel:
                return False

            content = msg.content.lower()
            if "yes" == content:
                answer = True
                return True

            if "no" == content:
                answer = False
                return True

            return False

        try:
            answermsg = await self.bot.wait_for('message', timeout=timeout, check=check)
            if delete_after:
                await answermsg.delete()
        except asyncio.TimeoutError:
            answer = None

        if delete_after:
            await message.delete()

        return answer

    async def ask(self, message=None, timeout=60, delete_after=True, author_id=None, allow_none=False, embed=None):
        """
        A function to ask a certain user for an answer using yes/no.

        :param embed: Another argument for the message.
        :param message: String for what the question is.
        :param timeout: How long the bot will wait for.
        :param delete_after: Should the message be deleted after?
        :param author_id: Who should respond. If None it will default to context author.
        :param allow_none: If they can respond with 'none'.
        :return: The author's answer. Returns None if timeout, and False if allow_none is on.
        """
        answer = None
        if message is None and embed is None:
            raise ValueError("Message and embed can't be NoneType!")

        message = await self.send(content=message, embed=embed)

        if author_id is None:
            author_id = self.author.id

        def check(msg):
            nonlocal answer
            if msg.author.id != author_id or msg.channel != message.channel:
                return False

            content = msg.content.lower()
            if "none" == content and allow_none:
                answer = False
                return True

            answer = msg.content
            return True

        try:
            answermsg = await self.bot.wait_for('message', timeout=timeout, check=check)
            if delete_after:
                await answermsg.delete()
        except asyncio.TimeoutError:
            answer = None

        if delete_after:
            await message.delete()

        return answer

    async def raw_ask(self, message=None, timeout=60, delete_after=True, author_id=None, allow_none=False, embed=None):
        """
        A function to ask a certain user for an answer using yes/no. Returns the message instead of the content.

        :param embed: Another argument for the message.
        :param message: String for what the question is.
        :param timeout: How long the bot will wait for.
        :param delete_after: Should the message be deleted after?
        :param author_id: Who should respond. If None it will default to context author.
        :param allow_none: If they can respond with 'none'.
        :return: The author's answer. Returns None if timeout, and False if allow_none is on.
        """
        answer = None
        if message is None and embed is None:
            raise ValueError("Message and embed can't be NoneType!")

        message = await self.send(content=message, embed=embed)

        if author_id is None:
            author_id = self.author.id

        def check(msg):
            nonlocal answer
            if msg.author.id != author_id or msg.channel != message.channel:
                return False

            content = msg.content.lower()
            if "none" == content and allow_none:
                answer = False
                return True

            answer = msg
            return True

        try:
            answermsg = await self.bot.wait_for('message', timeout=timeout, check=check)
            if delete_after:
                await answermsg.delete()
        except asyncio.TimeoutError:
            answer = None

        if delete_after:
            await message.delete()

        return answer

    async def show_help(self, command=None):
        cmd = self.bot.get_command('help')
        command = command or self.command.qualified_name
        await self.invoke(cmd, command=command)

    async def get_dm(self, user=None):
        if user is None:
            user = self.author
        if user.dm_channel is None:
            await user.create_dm()
        return user.dm_channel

    @property
    def db(self):
        if self.connection is None:
            self.acquire()
            return self.connection.cursor()
        else:
            return self.connection.cursor()

    def acquire(self):
        self.connection = db.MaybeAcquire()

    def release(self):
        if self.connection is not None:
            self.connection.release()

    async def clean(self, content, *, fix_channel_mentions=False, use_nicknames=False, escape_markdown=False,
                    escape_mentions=True, escape_roles=True):
        converter = CustomCleanContent(fix_channel_mentions=fix_channel_mentions, use_nicknames=use_nicknames,
                                       escape_markdown=escape_markdown, escape_mentions=escape_mentions,
                                       escape_roles=escape_roles)
        return await converter.convert(self, content)
