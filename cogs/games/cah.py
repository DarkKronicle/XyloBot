"""
Based off of Cards Against Humanity
https://cardsagainsthumanity.com
"""

from util.game import Game
import random
import discord
from discord.ext import commands
import asyncio
from storage.json_reader import JSONReader

cards = JSONReader("data/cah.json").data


class CAHUserInstance:

    def __init__(self, user, white_cards, max_cards=6):
        self.max_cards = max_cards
        self.user = user
        self.all_white_cards = white_cards
        self.white_cards = white_cards
        self.current_cards = random.sample(self.white_cards, max_cards)
        self.all_white_cards = list(set(self.all_white_cards) ^ set(self.current_cards))
        self.points = 0

    def add_point(self):
        self.points = self.points + 1

    def fill_cards(self):
        while len(self.current_cards) < self.max_cards:
            self.current_cards.append(random.choice(self.current_cards))

    def get_card_and_remove(self, num):
        self.fill_cards()
        if num > self.max_cards:
            num = 10
        if num < 1:
            num = 1
        card = self.current_cards[num - 1]
        self.current_cards.remove(card)
        return card

    async def send_white_cards(self, blackcard):
        if self.user.dm_channel is None:
            await self.user.create_dm()
        dm = self.user.dm_channel
        message = f"The current black card is:\n\n**{blackcard}**\n"
        i = 0
        for card in self.current_cards:
            i += 1
            message = message + f"\n**{i}:** {card}"
        message = message + "\n\nEnter the number of the card in the game channel!"
        embed = discord.Embed(title="White Cards", description=message, colour=discord.Colour.purple())
        await dm.send(embed=embed)


class CAHGameInstance(Game):
    instances = {}

    def __init__(self, channel, owner, done, categories, bot: commands.Bot):
        super().__init__(channel, owner)
        self.answering: discord.Message = None
        self.czar_answer = None
        self.bot = bot
        self.done = done
        self.categories = categories
        self.czar_num = 0
        self.needed_points = 5
        self.white_cards = self.get_white_cards()
        self.black_cards = self.get_black_cards()
        self.time = False
        self.answers = {}
        self.instances[owner] = CAHUserInstance(owner, self.white_cards)

    async def start(self, bot):
        await self.next_round(winner=None)

    def get_white_cards(self):
        white_cards = []
        for cat in self.categories:
            white_cards.extend(cards[cat]["white"])
        return white_cards

    def get_black_cards(self):
        black_cards = []
        for cat in self.categories:
            black_cards.extend(cards[cat]["black"])
        return black_cards

    async def add_user(self, user):
        super().add_user(user)
        self.instances[user] = CAHUserInstance(user, self.white_cards)

    async def end(self, user):
        await self.channel.send(f"{user.mention} won!!!!!!")
        self.done(self.bot)

    async def timeout(self):
        await self.channel.send("Looks like everyone doesn't want to play anymore :(")
        self.done(self.bot)

    def get_czar(self):
        return self.users[self.czar_num]

    def increment_czar(self):
        if self.czar_num >= len(self.users) - 1:
            self.czar_num = 0
            return
        self.czar_num = 0

    async def next_round(self, winner):
        if winner is not None:
            self.increment_czar()
            self.instances[winner].add_point()
            self.answers.clear()
            if self.instances[winner].points >= self.needed_points:
                await self.end(winner)
                return
        self.czar_answer = None
        black = random.choice(self.black_cards)
        if len(self.black_cards) < 2:
            self.black_cards = self.get_black_cards()
        await asyncio.sleep(3)
        await self.channel.send(
            embed=discord.Embed(title="New round!", description=f"The new card czar is {self.get_czar().mention}. The "
                                                                f"new black card is:\n\n`{black}`"))
        for user in self.instances:
            if user is not self.get_czar():
                await self.instances[user].send_white_cards(black)
        self.answering = await self.set_answering()
        self.time = True
        i = 0
        while not self.check_everyone() and i < 12:
            await asyncio.sleep(5)
            i = i + 1
        if len(self.answers) == 0:
            await self.timeout()
            return
        self.time = False
        message = "Time for the czar to answer!\n\n"
        j = 0
        for user in self.answers:
            j = j + 1
            message = message + f"**{j}:** {self.answers[user]}"
        await self.channel.send(message)
        self.answering = None
        i = 0
        while self.czar_answer is None and i < 12:
            await asyncio.sleep(5)
            i = i + 1
        if self.czar_answer is None:
            await self.timeout()
            return
        user = list(self.answers)[self.czar_answer-1]
        await self.channel.send(f"The czar enjoyed {user.mention}'s answer, which was: `{self.answers[user]}`")
        await self.next_round(user)

    def check_everyone(self):
        czar = self.get_czar()
        for user in self.users:
            if user not in self.answers and user is not czar:
                return False
        return True

    async def set_answering(self):
        message = "Make sure you answer here!\n\n"
        for user in self.answers:
            message = message + f"{user.display_name} - Answered!"
        if self.answering is None:
            return await self.channel.send(message)
        try:
            await self.answering.edit(content=message)
            return self.answering
        except:
            # TODO What is this error???
            self.answering = await self.channel.send(message)

    async def process_message(self, message: discord.Message):
        if message.author not in self.instances:
            return
        game: CAHUserInstance = self.instances[message.author]
        try:
            card_num = int(message.content)
        except ValueError:
            return
        await message.delete()
        if self.time:
            if self.get_czar() is not message.author:
                if message.author not in self.answers:
                    self.answers[message.author] = game.get_card_and_remove(card_num)
                    await self.set_answering()
        else:
            if message.author is self.get_czar() and self.czar_answer is None:
                if card_num >= len(self.answers):
                    card_num = len(self.answers)
                if card_num < 1:
                    card_num = 1
                self.czar_answer = card_num
