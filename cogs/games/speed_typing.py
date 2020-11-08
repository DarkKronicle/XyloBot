import asyncio
import random

import discord

from util import game


class QuizUserInstance:

    def __init__(self):
        self.points = 0

    def increment(self):
        self.points = self.points + 1


class QuizGameInstance(game.Game):

    def __init__(self, channel, owner, done, questions=None, max_score=5):
        super().__init__(channel, owner)

    async def start(self, bot):
        self.started = True
        await self.round(bot)

    async def timeout(self):
        pass

    async def end(self, user):
        await self.done(self.channel)

    async def round(self, bot):
        channel = self.channel
        users = self.users

        def check(msg: discord.Message):
            nonlocal channel
            nonlocal answer
            nonlocal users
            if msg.author not in users or msg.channel != channel:
                return False
            else:
                if msg.content.lower() in answer.lower():
                    return True
            return False

        try:
            go = await bot.wait_for("message", timeout=120, check=check)
            await asyncio.sleep(3)
            await self.end(go.author)
        except asyncio.TimeoutError:
            await self.timeout()

    async def process_message(self, message):
        if not self.answering or self.winner is not None:
            return
        try:
            await message.delete()
        except discord.HTTPException:
            pass
        self.active = True
        if message.content.lower() == self.answer.lower():
            self.winner = message.author
            await message.channel.send(f"{message.author.mention} got it right!", delete_after=5)
        else:
            await message.channel.send("Incorrect answer!", delete_after=5)
