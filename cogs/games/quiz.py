import random

from util import game


class QuizUserInstance:
    pass


class QuizGameInstance(game.Game):

    def __init__(self, channel, owner, questions: dict):
        super().__init__(channel, owner)
        self.questions = questions

    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)

    async def start(self, bot):
        self.started = True

    async def timeout(self):
        pass

    async def end(self, user):
        pass

    async def round(self):
        card = random.choice(self.questions)
        answer = self.questions[card]

    async def process_message(self, message):
        pass
