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

    async def show_help(self, command=None):
        cmd = self.bot.get_command('help')
        command = command or self.command.qualified_name
        await self.invoke(cmd, command=command)

