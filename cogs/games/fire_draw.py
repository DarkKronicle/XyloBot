import discord
from util.Game import Game
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
        answer = get_random_string(5)
        message = await self.channel.send("Ready?")
        await asyncio.sleep(2)
        await message.edit(content="     {} \u200b {}")
        await asyncio.sleep(0.5)
        await message.edit(content="    {}   \u200b   {}")
        await asyncio.sleep(0.5)
        await message.edit(content="   {}   \u200b      {}")
        await asyncio.sleep(0.5)
        await message.edit(content="  {}     \u200b       {}")
        await asyncio.sleep(random.randint(1, 8))
        await message.edit(content=f"Type in `{answer}` as quickly as possible!")

        def check(msg: discord.Message):
            if msg.author not in self.users:
                return False
            if msg.author in self.users and msg.channel == self.channel and msg.content.lower() == answer.lower():
                return True
            return False

        try:
            go = await bot.wait_for("message", timeout=10, check=check)
            await asyncio.sleep(1)
            await self.end(go.author)
        except asyncio.TimeoutError:
            await self.timeout()

    async def end(self, user):
        await self.channel.send(f"{user.mention} wins!")

    async def timeout(self):
        await self.channel.send("Right before the duel was about to take place, everyone left and no one shot...")
