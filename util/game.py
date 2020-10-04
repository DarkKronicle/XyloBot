import discord


class Game:
    users = []

    def __init__(self, channel, owner):
        self.channel: discord.TextChannel = channel
        self.owner: discord.User = owner
        self.users.append(owner)
        self.started = False

    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)

    async def start(self, bot):
        pass

    async def timeout(self):
        pass

    async def end(self, user):
        pass
