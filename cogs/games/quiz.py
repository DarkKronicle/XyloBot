import asyncio
import random

import discord

from util import game

questio = {
    "Who's awesome?": "DarkKronicle",
    "Are you cool?": "No",
    "Am I cool?": "Yes",
    "Are you a nerd?": "Yes",
    "How many commits does xylo have?": "500",
    "Lots of questions": "YES"
}


class QuizUserInstance:

    def __init__(self):
        self.score = 0

    def increment(self):
        self.score = self.score + 1

    def score(self):
        return self.score


class QuizGameInstance(game.Game):

    def __init__(self, channel, owner, done, questions=None, max_score=5):
        super().__init__(channel, owner)
        if questions is None:
            questions = questio
        self.questions = questions
        self.winner = None
        self.answer = None
        self.question = None
        self.answers = {}
        self.active = False
        self.instances = {}
        self.max_score = max_score
        self.done = done

    def add_user(self, user):
        self.users.append(user)
        self.instances[user] = QuizUserInstance()

    def remove_user(self, user):
        self.users.remove(user)

    async def start(self, bot):
        self.started = True
        await self.round()

    async def timeout(self):
        pass

    async def end(self, user):
        await self.done(self.channel.guild)
        pass

    async def round(self):
        self.question = random.choice(list(self.questions))
        self.answer = self.questions[self.question]
        self.winner = None
        i = 0
        self.active = False
        embed = discord.Embed(
            title="Quiz!",
            description=f"Question is: `{self.question}`",
            colour=discord.Colour.blue()
        )
        while i < 12 and self.winner is None:
            i = i + 1
            await asyncio.sleep(5)
        if self.winner is None:
            embed = discord.Embed(
                title="No one got the answer!",
                description=f"Question: `{self.question}`.\n\nAnswer: `{self.answer}`"
            )
            if self.active is False:
                self.done()
                return await self.channel.send("No one has done anything ;-;")
            await self.channel.send(embed=embed)
            await self.round()
            return

        embed = discord.Embed(
            title="Round Over!",
            description=f"{self.winner.mention} got the right answer `{self.answer}`!"
        )
        await self.channel.send(embed=embed)
        win = self.instances[self.winner]
        win.increment()
        if win.score() >= self.max_score:
            return await self.channel.send(f"{self.winner.mention} won!")

    async def process_message(self, message):
        await message.delete()
        self.active = True
        if message.content.lower() == self.answer.lower():
            await message.channel.send(f"{message.author.mention} got it right!")
            self.winner = message.author
        else:
            await message.channel.send("Incorrect answer!", delete_after=5)
