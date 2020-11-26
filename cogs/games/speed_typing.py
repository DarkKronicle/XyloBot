import asyncio
from fuzzywuzzy import fuzz

import discord

from cogs.random_commands import RandomCommands
from util import game


def anti_copy(string):
    chars = list(string)
    c = 0
    for i in range(len(chars.copy())):
        c = c + 1
        if i % 5 != 0:
            continue
        c = c + 1
        chars.insert(c, '\u200b')

    return ''.join(chars)


class SpeedTypingInstance(game.Game):

    def __init__(self, channel, owner, *, message=None):
        super().__init__(channel, owner)
        if message is None or message == "":
            message = RandomCommands.get_random_lines(5).replace("\n", " ").replace("    ", "").replace("  ", " ")
            message = message.replace("@", "[@]")
            if message.endswith(" "):
                message = message[:len(message)-1]
            if message.startswith(" "):
                message = message[1:]
            if len(message) > 1900:
                message = message[:1900]
            self.message = message
        else:
            self.message = message

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

        start_msg = await channel.send(f"Type this as fast as you can!\n\n```PYTHON\n{anti_copy(self.message)}\n```")

        def check(msg: discord.Message):
            nonlocal channel
            nonlocal users
            if msg.author not in users or msg.channel != channel:
                return False
            else:
                return True

        start_time = start_msg.created_at
        try:
            go = await bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            await self.timeout()
            await channel.send("Timed out.")
            return
        end_time = go.created_at
        total_seconds = (end_time - start_time).total_seconds()
        text = go.content
        accuracy = fuzz.ratio(self.message, text)
        wpm = len(text) / (5 * (total_seconds / 60))
        await channel.send(embed=discord.Embed(
            title="Results",
            description=f"You finished after `{round(total_seconds)}` seconds, typed at a speed of `{round(wpm)} WPM`, and an accuracy of `{accuracy}%`",
            colour=discord.Colour.gold()
        ))
        await self.end(go.author)

    async def process_message(self, message):
        pass
