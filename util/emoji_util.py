from discord.ext import commands
from storage.config import JSONReader
import random


all_emojis: dict = JSONReader("data/emojis.json").data


emoji_list = []

for _, emoji in all_emojis.items():
    diversity = emoji.get("diversity")
    if diversity is None:
        emoji_list.append(emoji["emoji"])
    else:
        emoji_list.extend([e for _, e in emoji["diversity"].items()])

all_emoji_data: dict = {k: v["emoji"] for k, v in all_emojis.items()}


class StandardEmoji(commands.Converter):
    async def convert(self, ctx, argument):
        """
        # 1 - Check if unicode emoji
        # 2 - Check if it's name is in discord found
        """

        if argument in all_emoji_data.values():
            return argument

        argument = argument.lower()
        if argument in all_emoji_data.keys():
            return all_emoji_data[argument]

        return None

async def random_reaction(message):
    emojis = random.choice(emoji.emoji_list)
    try:
        await message.add_reaction(emojis)
    except:
        pass
    return emojis