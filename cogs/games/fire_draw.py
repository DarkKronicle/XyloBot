import discord
from util.Game import Game
import random
import asyncio
from discord.ext import commands


class FireDrawGame(Game):
    def __init__(self, channel, owner):
        super().__init__(channel, owner)

    async def start(self, bot: commands.Bot):
        message = await self.channel.send("Ready?")
        await asyncio.sleep(2)
        await message.edit(content="     :smirk: :unamused:")
        await asyncio.sleep(0.5)
        await message.edit(content="    :smirk:   :unamused:")
        await asyncio.sleep(0.5)
        await message.edit(content="   :smirk:     :unamused:")
        await asyncio.sleep(0.5)
        await message.edit(content="  :smirk:      :unamused:")
        await asyncio.sleep(random.randint(1, 8))
        await message.edit(content="***GOOOOOO!!!***")

        def check(msg: discord.Message):
            if msg.author not in self.users:
                return False
            if msg.author in self.users and msg.channel == self.channel:
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
