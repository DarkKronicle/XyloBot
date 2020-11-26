import discord

from cogs.random_commands import RandomCommands
from util.game import Game
import random
import asyncio
from discord.ext import commands
import string
import cogs.games.speed_typing


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


class FireDrawGame(Game):
    emojis = [":grinning:", ":triumph:", ":cold_face:", ":rage:", ":nauseated_face:", ":confused:", ":yawning_face:"]

    def __init__(self, channel, owner, *, rand_lines=False):
        super().__init__(channel, owner)
        self.rand_lines = rand_lines

    text = [
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "i am better than you",
        "pog champ",
        "abcdefghijklmnopqrstuvwxyz",
        "gottem",
        "boi",
        "ez",
        "ez dub for the champion"
           ]

    async def start(self, bot: commands.Bot):
        self.started = True
        answer = ""
        backup = True
        if self.rand_lines:
            answer = RandomCommands.get_random_lines(1).replace("\n", " ").replace("    ", "").replace("  ", " ")
            answer = answer.replace("@", "[@]")
            if answer.endswith(" "):
                answer = answer[:len(answer) - 1]
            if answer.startswith(" "):
                answer = answer[1:]
            if len(answer) > 500:
                answer = answer[:500]
            backup = len(answer) < 5
        if backup:
            if random.randint(0, 100) > 90:
                answer = random.choice(self.text)
            else:
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
        await message.edit(content=f"Type in `{cogs.games.speed_typing.anti_copy(answer)}` as quickly as possible!")
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
            go = await bot.wait_for("message", timeout=30, check=check)
            await asyncio.sleep(3)
            await self.end(go.author)
        except asyncio.TimeoutError:
            await self.timeout()

    async def end(self, user):
        await self.channel.send(f"{user.mention} emerges victorious!")

    async def timeout(self):
        await self.channel.send("Right before the duel was about to take place, everyone left and no one shot...")

    async def process_message(self, message):
        try:
            await message.delete()
        except discord.HTTPException:
            pass
