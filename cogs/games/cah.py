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
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

cards = JSONReader("data/cah.json").data


# https://itnext.io/how-to-wrap-text-on-image-using-python-8f569860f89e
def text_wrap(text, font, max_width):
    """Wrap text base on specified width.
    This is to enable text of width more than the image width to be display
    nicely.

    @params:
        text: str
            text to wrap
        font: obj
            font of the text
        max_width: int
            width to split the text with
    @return
        lines: list[str]
            list of sub-strings
    """
    lines = []

    # If the text width is smaller than the image width, then no need to split
    # just add it to the line list and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than the image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            lines.append(line)
    return lines


def black_card(blackcard):
    image = Image.open("assets/cah/blackcard.png")

    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype("assets/FontsFree-Net-SFProDisplay-Bold.ttf", 240)

    line_height = font.getsize('hg')[1]
    lines = text_wrap(blackcard, font, 1800)
    y = 5
    for line in lines:
        draw.text((30, y), line, fill="white", font=font, align="left")
        y = y + line_height

    buffer = BytesIO()
    image.save(buffer, "png")
    buffer.seek(0)
    return discord.File(fp=buffer, filename="blackcard.png")


class CAHUserInstance:
    """
    Handles player information.
    """

    def __init__(self, user, white_cards, max_cards=6):
        self.max_cards = max_cards
        self.user = user
        self.all_white_cards = white_cards
        self.white_cards = white_cards
        self.current_cards = random.sample(self.white_cards, max_cards)
        self.white_cards = list(set(self.white_cards) ^ set(self.current_cards))
        self.points = 0

    def add_point(self):
        self.points = self.points + 1

    def fill_cards(self):
        while len(self.current_cards) < self.max_cards + 1:
            # Get new card and remove from player "deck". Prevents repeats.
            new_card = random.choice(self.white_cards)
            self.white_cards.remove(new_card)
            if len(self.white_cards) < 1:
                self.white_cards = self.all_white_cards
            self.current_cards.append(new_card)

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
        message = f"The current black card is:\n\n`{blackcard}`\n"
        i = 0
        for card in self.current_cards:
            i += 1
            message = message + f"\n**{i}:** {card}"
        message = message + "\n\nEnter the number of the card in the game channel!"
        embed = discord.Embed(title="Cards Against Humanity - White Cards", description=message,
                              colour=discord.Colour.purple())
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
        # Randomize card czar somewhat.
        random.shuffle(self.users)
        self.started = True
        await self.next_round()

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
        embed = discord.Embed(
            title="Cards Against Humanity - Winner!",
            description=f"{user.mention} won the game!",
            colour=discord.Colour.green()
        )
        await self.channel.send(embed=embed)
        await self.done(self.bot)

    async def timeout(self):
        out = discord.Embed(
            title="Game Ended",
            description="This game has not had any activity in the past minute and has timed out.",
            colour=discord.Colour.red()
        )
        await self.channel.send(embed=out)
        await self.done(self.bot)

    def get_czar(self):
        return self.users[self.czar_num]

    def increment_czar(self):
        if self.czar_num >= len(self.users) - 1:
            self.czar_num = 0
            return
        self.czar_num = self.czar_num + 1

    async def next_round(self):
        # Remove the last czar answer and select black card for the round.
        self.czar_answer = None
        black: str = random.choice(self.black_cards)
        self.black_cards.remove(black)
        if len(self.black_cards) < 1:
            self.black_cards = self.get_black_cards()

        # Discord will format it to use underscores, we just want the default.
        await asyncio.sleep(3)
        embed = discord.Embed(
                title="New round!",
                description=f"The new card czar is {self.get_czar().mention}. The new black card is:\n\n`{black}`",
                colour=discord.Colour.purple()
            )
        await self.channel.send(
            embed=embed,
            file=black_card(black)
        )
        for user in self.instances:
            if user is not self.get_czar():
                await self.instances[user].send_white_cards(black)

        # Message for who has answered what.
        self.answering = await self.set_answering()
        # Is it time for users to submit answers?
        self.time = True

        # Loop for one minute checking every 5 seconds if everyone has answered.
        i = 0
        while not self.check_everyone() and i < 12:
            await asyncio.sleep(5)
            i = i + 1

        # It will work with just 1 answer, but 0 answers will break.
        if len(self.answers) == 0:
            await self.timeout()
            return

        await self.answering.delete()
        self.answering = None

        self.time = False

        # Don't want the czar to know who's is who...
        answer_list = list(self.answers.items())
        random.shuffle(answer_list)
        self.answers = dict(answer_list)

        embed = discord.Embed(
            title=f"Time for the czar to choose!"
        )
        embed.set_footer(text="You have one minute to answer.")
        message = f"Type in your answer {self.get_czar().mention}!\n\n"
        current_answer = 0
        for user in self.answers:
            current_answer = current_answer + 1
            message = message + f"**{current_answer}:** {self.answers[user]}\n"
        embed.description = message
        await self.channel.send(embed=embed)

        # Wait for czar to answer
        i = 0
        while self.czar_answer is None and i < 12:
            await asyncio.sleep(5)
            i = i + 1

        if self.czar_answer is None:
            # Didn't answer...
            await self.timeout()
            return

        # Get winner through number
        winner = list(self.answers)[self.czar_answer - 1]

        winner_embed = discord.Embed(
            title=f"The czar chose!",
            description=f"The winner was {winner.mention}!\n\nBlack card: `{black}`\n\nAnswer: `{self.answers[winner]}`",
            colour=discord.Colour.magenta()
        )
        await self.channel.send(embed=winner_embed)
        self.instances[winner].add_point()

        points_embed = discord.Embed(
            colour=discord.Colour.dark_purple()
        )
        points_embed.set_author(name="Current Points")
        message = ""
        for user in self.instances:
            game = self.instances[user]
            message = message + f"{user.display_name} - **{game.points}**\n"
        points_embed.description = message
        await self.channel.send(embed=points_embed)

        self.increment_czar()
        self.answers.clear()

        if self.instances[winner].points >= self.needed_points:
            await self.end(winner)
            return

        await self.next_round()

    def check_everyone(self):
        """
        Checks if everyone but czar answered.
        """
        czar = self.get_czar()
        for user in self.users:
            if user not in self.answers and user is not czar:
                return False
        return True

    async def set_answering(self):
        """
        Sets the answer for answering message.
        """
        embed = discord.Embed(
            colour=discord.Colour.dark_purple()
        )
        embed.set_footer(text="You have one minute to answer.")
        embed.set_author(name="Current Answers")
        message = "Make sure you answer here!\n\n"
        czar = self.get_czar()
        for user in self.users:
            if user is czar:
                continue
            if user not in self.answers:
                message = message + f":no_entry_sign:  - `{user.display_name}`\n"
            else:
                message = message + f":white_check_mark:  - `{user.display_name}`\n"
        embed.description = message
        if self.answering is None:
            return await self.channel.send(embed=embed)
        try:
            await self.answering.edit(embed=embed)
            return self.answering
        except:
            # TODO What is this error???
            self.answering = await self.channel.send(embed=embed)

    async def process_message(self, message: discord.Message):
        """
        Processes messages that happen in the channel.
        """
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
