import discord
import scrython
from discord.ext import menus

from util import queue
import cogs.mtg
from util.mtg_pages.search import CardSearch


class AdvancedSearch(menus.Menu):

    @classmethod
    def create_button_func(cls, name, desc, question, func):
        async def button_func(self, payload):
            answer = await self.ctx.ask(question)
            if answer is not None:
                self.query[name] = func(answer)

        button_func.__doc__ = desc
        return button_func

    def __init__(self, queue):
        super().__init__(check_embeds=True)
        self.queue = queue
        self.query = {
            "types": None,
            "is": None,
            "card_name": None,
            "card_text": None,
            "colors": None,
            "cmc": None,
            "cost": None,
            "rarity": None,
            "price": None
        }

        def type_convert(s):
            splits = s.split(" ")
            formatted = []
            for split in splits:
                if split.startswith("-") and len(split) > 1:
                    formatted.append(f"-t:{split[1:]}")
                elif len(split) > 1:
                    formatted.append(f"t:{split}")
            return " ".join(formatted)

        def is_convert(s):
            splits = s.split(" ")
            formatted = []
            for split in splits:
                if split.startswith("-") and len(split) > 2:
                    formatted.append(f"-is:{split[2:]}")
                elif len(split) > 1:
                    formatted.append(f"is:{split}")
            return " ".join(formatted)

        def text_convert(s):
            s = s.replace('"', r'\"')
            return f'o:"{s}"'

        def cmc_convert(s):
            if s.startswith(">") or s.startswith("<"):
                return f"cmc{s}"
            if s.startswith("=") and len(s) > 1:
                return f"cmc:{s[1:]}"
            return f"cmc:{s}"

        def c_convert(s):
            if s.startswith(">") or s.startswith("<"):
                return f"m{s}"
            if s.startswith("=") and len(s) > 1:
                return f"m:{s[1:]}"
            return f"m:{s}"

        def r_convert(s):
            s = s.lower()
            if s not in ("common", "uncommon", "rare", "mythic"):
                return None
            if s.startswith(">") or s.startswith("<"):
                return f"r{s}"
            if s.startswith("=") and len(s) > 1:
                return f"r:{s[1:]}"
            return f"r:{s}"

        def p_convert(s):
            if s.startswith(">") or s.startswith("<"):
                return f"usd{s}"
            if s.startswith("=") and len(s) > 1:
                return f"usd:{s[1:]}"
            return f"usd:{s}"

        to_add = [
            ("card_name", "📝", "Card Name", "What name of card do you want to search for? (Can be incomplete)",
             lambda s: s),

            ("si", "ℹ️", "Card Types",
             "What should the card be? Seperate using ` ` and put `-` in front if you don't want that. (Example `funny`, `hybrid`...)",
             type_convert),

            ("is", "💡", "Card Is", "What type of card should it be? Seperate using ` ` and put `-` in front if "
             "you don't want that.", is_convert),

            ("card_text", "📑", "Card Text", "What text should be in the card? Use `~` as a placeholder for the card "
             "name.", text_convert),

            ("colors", "◻️", "Card Colors",
             "What colors should the card be? (Use `RUBGW`. You can also use `>`, `>=`, `<`, `<=`)",
             lambda s: f"c:{s}"),

            ("cmc", "👓", "CMC", "What should the calculated mana cost be? You can use `>`, `>=`, `<`, `<=` or `=`.",
             cmc_convert),

            ("cost", "🛄", "Mana Cost",
             "What mana cost should I look for? (Use color codes. Example: `3WRR`. 3 generic mana with one white and two red. You can also use `>`, `>=`, `<`, `<=`)",
             c_convert),

            (
            "rarity", "🏆", "Rarity", "What rarity? (Common, uncommon, rare, mythic. You can use `>`, `>=`, `<`, `<=`)",
            r_convert),

            ("price", "🤑", "Price", "What price should the card be? (In USD. You can use `>`, `>=`, `<`, `<=`)",
             p_convert)
        ]
        for name, emoji, desc, question, func in to_add:
            self.add_button(menus.Button(emoji, self.create_button_func(name, desc, question, func)))

    async def finalize(self, timed_out):
        try:
            await self.message.delete()
        except discord.HTTPException:
            pass

    @menus.button("❌", position=menus.First(1))
    async def stop_search(self, payload):
        """discard search"""
        self.stop()

    @menus.button("✅", position=menus.First(0))
    async def send_search(self, payload):
        """searches what you have set"""
        searches = []
        for s in self.query.values():
            if s is not None:
                searches.append(s)
        if len(searches) == 0:
            return await self.ctx.send("You didn't specify anything!")
        search = " ".join(searches)
        async with self.ctx.typing():
            async with queue.QueueProcess(queue=self.queue):
                try:
                    cards = scrython.cards.Search(q=search)
                    await cards.request_data()
                except scrython.foundation.ScryfallError as e:
                    return await self.ctx.send(e.error_details["details"])
        if len(cards.data()) == 0:
            return await self.ctx.send("No cards with that name found.")
        try:
            p = CardSearch([cogs.mtg.Searched(c) for c in cards.data()], search)
            await p.start(self.ctx)
        except menus.MenuError as e:
            await self.ctx.send(e)
            return

    async def send_initial_message(self, ctx, channel):
        description = "Welcome to *Advanced Search!* React using the following emoji key to specify the query. You can " \
                      "the normal search command using https://scryfall.com/docs/syntax for even more control!\n\n" \
                      "*If it says it ignored your search query you typed something in invalid."
        embed = discord.Embed(colour=discord.Colour.magenta(), description=description)
        messages = []
        for (emoji, button) in self.buttons.items():
            messages.append(f'{emoji}: {button.action.__doc__}')

        embed.add_field(name='What do these reactions do?', value='\n'.join(messages), inline=False)
        return await channel.send(embed=embed)