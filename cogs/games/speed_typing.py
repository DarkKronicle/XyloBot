import asyncio

import discord

from cogs.random_commands import RandomCommands
from util import game


class SpeedTypingInstance(game.Game):

    def __init__(self, channel, owner):
        super().__init__(channel, owner)

    async def start(self, bot):
        self.started = True
        await self.round(bot)

    async def timeout(self):
        pass

    async def end(self, user):
        pass

    async def round(self, bot):
        channel = self.channel
        users = self.users
        message = RandomCommands.get_random_lines(10).replace("\n", " ")
        for i in range(5):
            message = message.replace("  ", " ")
        if len(message) > 1900:
            message = message[:1900]
        start_msg = await channel.send(f"Type this as fast as you can!\n\n```PYTHON\n{message}\n```")
        start_time = start_msg.created_at.microsecond / 1000

        def check(msg: discord.Message):
            nonlocal channel
            nonlocal users
            if msg.author not in users or msg.channel != channel:
                return False
            else:
                return True

        try:
            go = await bot.wait_for("message", timeout=120, check=check)
            await asyncio.sleep(3)
        except asyncio.TimeoutError:
            await self.timeout()
            await channel.send("Timed out.")
            return
        end_time = go.created_at.microsecond / 1000
        total_minutes = (end_time - start_time) / 1000 / 60
        text = go.content
        count = 0
        for i, c in enumerate(message):
            if i >= len(text):
                break
            try:
                if text[i] == c:
                    count += 1
            except IndexError:
                break
        accuracy = round(count / len(message) * 100)
        wpm = len(text) * 60 / (5 * total_minutes)
        await channel.send(embed=discord.Embed(
            title="Results",
            description=f"You typed at a speed of `{wpm} WMP`, and an accuracy of `{accuracy}%`",
            colour=discord.Colour.gold()
        ))
        await self.end(go.author)

    async def process_message(self, message):
        pass
