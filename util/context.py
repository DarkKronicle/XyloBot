"""
This class was heavily based off of https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/cogs/utils/context.py#L23:1
Rapptz is amazing.
The code above was released under MIT license.
"""

from discord.ext import commands
import asyncio


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def prompt(self, message, timeout=60, delete_after=True, author_id=None):
        """
        A function to ask a certain user for an answer using yes/no.

        :param message: String for what the question is.
        :param timeout: How long the bot will wait for.
        :param delete_after: Should the message be deleted after?
        :param author_id: Who should respond. If None it will default to context author.
        :return: True if yes, false if no, None if timeout.
        """

        message = await self.send(message)

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

            await self.send("Reply with `yes` or `no`!", delete_after=10)
            return False

        try:
            await self.bot.wait_for(message=message, timeout=timeout, check=check)
        except asyncio.TimeoutError:
            answer = None

        if delete_after:
            await message.delete()

        return answer

    async def ask(self, message, timeout=60, delete_after=True, author_id=None, allow_none=False):
        """
        A function to ask a certain user for an answer using yes/no.

        :param message: String for what the question is.
        :param timeout: How long the bot will wait for.
        :param delete_after: Should the message be deleted after?
        :param author_id: Who should respond. If None it will default to context author.
        :param allow_none: If they can respond with 'none'.
        :return: The author's answer. Returns None if timeout, and False if allow_none is on.
        """

        message = await self.send(message)

        answer = None

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
            await self.bot.wait_for(message=message, timeout=timeout, check=check)
        except asyncio.TimeoutError:
            answer = None

        if delete_after:
            await message.delete()

        return answer
