import discord
from util.game import Game
import random
import asyncio
from discord.ext import commands
import string


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


class FireDrawGame(Game):
    emojis = [":grinning:", ":triumph:", ":cold_face:", ":rage:", ":nauseated_face:", ":confused:", ":yawning_face:"]

    def __init__(self, channel, owner):
        super().__init__(channel, owner)

    async def start(self, bot: commands.Bot):
        answer = get_random_string(random.randint(4, 10))
        message = await self.channel.send("Ready?")
        emoji1 = random.choice(self.emojis)
        emoji2 = random.choice(self.emojis)
        await asyncio.sleep(2)
        await message.edit(content="\u200b         {}{}".format(emoji1, emoji2))
        await asyncio.sleep(0.5)
        await message.edit(content="\u200b      {}      {}".format(emoji1, emoji2))
        await asyncio.sleep(0.5)
        await message.edit(content="\u200b   {}            {}".format(emoji1, emoji2))
        await asyncio.sleep(0.5)
        await message.edit(content="\u200b{}                  {}".format(emoji1, emoji2))
        await asyncio.sleep(random.randint(1, 8))
        await message.edit(content=f"Type in `{answer}` as quickly as possible!")
        channel = self.channel
        users = self.users

        def check(msg: discord.Message):
            nonlocal channel
            nonlocal answer
            nonlocal users
            if msg.author not in users or msg.channel != channel:
                return False
            if msg.content.lower() in answer.lower():
                return True
            return False

        try:
            go = await bot.wait_for("message", timeout=10, check=check)
            await asyncio.sleep(3)
            await self.end(go.author)
        except asyncio.TimeoutError:
            await self.timeout()

    async def end(self, user):
        await self.channel.send(f"{user.mention} emerges victorious!")

    async def timeout(self):
        await self.channel.send("Right before the duel was about to take place, everyone left and no one shot...")
