import asyncio

import discord
import scrython
from discord.ext import menus
import enum

from scrython.cards.cards_object import CardsObject
from functools import partial

import cogs.mtg
from util import queue
from util.paginator import Pages


def append_exists(message, **kwargs):
    for k, v in kwargs.items():
        if isinstance(v, tuple):
            m = v[0]
            suffix = v[1]
        else:
            m = v
            suffix = ""
        if m is None:
            continue
        message = message + f"**{k}:** {m}{suffix}\n"
    return message


def color_from_card(card):
    try:
        if card.colors() is None:
            return discord.Colour.light_gray()
        try:
            color = card.colors()[0]
        except IndexError:
            color = card.colors()
    except KeyError:
        return discord.Colour.light_grey()
    if color == "W":
        return discord.Colour.lighter_gray()
    if color == "U":
        return discord.Colour.blue()
    if color == "R":
        return discord.Colour.red()
    if color == "B":
        return discord.Colour.darker_grey()
    if color == "G":
        return discord.Colour.green()
    return discord.Colour.dark_grey()


def card_image_embed(card: CardsObject):
    description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=(card.prices("usd"), "$"))
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Image", url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_image(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


def card_prices_embed(card: CardsObject):
    description = card.rarity()
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Prices", url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    embed.add_field(name="USD", value=f"${card.prices('usd')}")
    embed.add_field(name="USD Foil", value=f"{card.prices('usd_foil')}")
    embed.add_field(name="EUR", value=f"€{card.prices('eur')}")
    embed.add_field(name="TIX", value=f"{card.prices('tix')}")
    return embed


def card_legal_embed(card: CardsObject):
    description = append_exists("", Set=card.set_name(), CMC=card.cmc(), Price=(card.prices("usd"), "$"))
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Legalities", url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())

    legal = card.legalities()

    def pretty(form, val):
        return form.capitalize(), val.replace("_", " ").capitalize()

    for k, v in legal.items():
        name, value = pretty(k, v)
        embed.add_field(name=name, value=value)

    return embed


def card_text_embed(card: CardsObject):
    # https://github.com/NandaScott/Scrython/blob/master/examples/get_and_format_card.py
    if "Creature" in card.type_line():
        pt = "({}/{})".format(card.power(), card.toughness())
    else:
        pt = ""

    if card.cmc() == 0:
        mana_cost = ""
    else:
        mana_cost = card.mana_cost()

    description = """
    `{mana_cost}`   -    {set_code}
    {type_line}

    {oracle_text} {power_toughness}
    *{rarity}*
    """.format(
        cardname=card.name(),
        mana_cost=mana_cost,
        type_line=card.type_line(),
        set_code=card.set_name(),
        rarity=card.rarity().capitalize(),
        oracle_text=card.oracle_text(),
        power_toughness=pt
    ).replace("    ", "")
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    embed.set_author(name=card.name() + " - Text", url=card.scryfall_uri())
    url = card.image_uris(0, "large")
    if url is not None:
        embed.set_thumbnail(url=str(url))
    if card.released_at() is not None:
        embed.set_footer(text=card.released_at())
    return embed


class CardView(enum.Enum):
    image = partial(card_image_embed)
    text = partial(card_text_embed)
    legalities = partial(card_legal_embed)
    prices = partial(card_prices_embed)


class CardSearchSource(menus.ListPageSource):

    def __init__(self, entries, *, per_page=15):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu, entries):
        embed = discord.Embed(colour=discord.Colour.magenta())
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f"**{index + 1}.** {entry.name()}")

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries.)"
            embed.set_footer(text=footer)

        embed.description = '\n'.join(pages)
        if len(menu.query) > 20:
            q = menu.query[:20] + "..."
        else:
            q = menu.query
        embed.set_author(name=f"Search Results For: {q}")
        embed.colour = discord.Colour.magenta()
        menu.embed = embed
        return menu.embed

    async def format_card(self, menu, card):
        view = menu.view_type
        embed = view.value(card)
        embed.set_footer(text=f"{embed.footer.text} - Showing card {menu.current_card + 1}/{len(self.entries)}")
        menu.embed = embed
        return menu.embed

    def is_paginating(self):
        # We always want buttons so that we can view card information.
        return True


class CardSearch(Pages):
    """
    A menu that consists of two parts, the list of all cards, then the in depth card view on each.
    """

    def __init__(self, entries, query, *, per_page=15):
        super().__init__(CardSearchSource(entries, per_page=per_page))
        self.embed = discord.Embed(colour=discord.Colour.magenta())
        self.entries = entries
        self.current_card = 0
        self.card_view = False
        self.query = query
        self.view_type = CardView.image

    def _skip_singles(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None or max_pages <= 1:
            max_cards = len(self.entries)
            if max_cards <= 1:
                return True
            return False
        else:
            return False

    def _skip_doubles(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None or max_pages <= 2:
            max_cards = len(self.entries)
            if max_cards <= 2:
                return True
            return False
        else:
            return False

    async def show_page(self, page_number):
        self.card_view = False
        await super().show_page(page_number)

    @menus.button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
                  position=menus.First(0), skip_if=_skip_doubles)
    async def go_to_first_page(self, payload):
        """go to the first page"""
        """go to the last page"""
        if not self.card_view:
            await self.show_checked_page(0)
        else:
            await self.show_card_page(0)

    @menus.button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f', position=menus.First(1))
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        if not self.card_view:
            await self.show_checked_page(self.current_page - 1)
        else:
            await self.show_card_page(self.current_card - 1)

    @menus.button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f', position=menus.Last(0))
    async def go_to_next_page(self, payload):
        """go to the next page"""
        if not self.card_view:
            await self.show_checked_page(self.current_page + 1)
        else:
            await self.show_card_page(self.current_card + 1)

    @menus.button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
                  position=menus.Last(1), skip_if=_skip_doubles)
    async def go_to_last_page(self, payload):
        """go to the last page"""
        if not self.card_view:
            await self.show_checked_page(self._source.get_max_pages() - 1)
        else:
            await self.show_card_page(len(self.entries) - 1)

    @menus.button('🔄', position=menus.Last(4))
    async def go_to_last_page(self, payload):
        """rotate through different card views"""
        order = [CardView.image, CardView.text, CardView.legalities, CardView.prices]
        num = order.index(self.view_type) + 1
        if num >= len(order):
            self.view_type = order[0]
        else:
            self.view_type = order[num]
        if self.card_view:
            await self.show_card_page(self.current_card)

    @menus.button('↩️', position=menus.Last(2))
    async def go_current_page(self, payload):
        """switch page view to card view"""
        if self.card_view:
            await self.show_checked_page(self.current_page)
        else:
            await self.show_card_page(self.current_card)

    @menus.button('📑', position=menus.Last(3))
    async def card_info(self, payload):
        """view information on a card"""
        channel = self.message.channel
        author_id = payload.user_id
        to_delete = [await channel.send('What number card do you want information on?')]

        def message_check(m):
            return m.author.id == author_id and \
                   channel == m.channel and \
                   m.content.isdigit()

        try:
            msg = await self.bot.wait_for('message', check=message_check, timeout=30.0)
        except asyncio.TimeoutError:
            to_delete.append(await channel.send('This has been closed due to a timeout.'))
            await asyncio.sleep(5)
        else:
            number = int(msg.content)
            to_delete.append(msg)
            await self.show_card_page(number - 1)

        try:
            await channel.delete_messages(to_delete)
        except Exception:
            pass

    async def show_card_page(self, card_number):
        max_cards = len(self.entries)
        try:
            if max_cards is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_card(card_number)
            elif max_cards > card_number >= 0:
                await self.show_card(card_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def _get_kwargs_from_card(self, card):
        value = await discord.utils.maybe_coroutine(self._source.format_card, self, card)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}

    async def show_card(self, card_number):
        self.card_view = True
        card = self.entries[card_number]
        self.current_card = card_number
        kwargs = await self._get_kwargs_from_card(card)
        await self.message.edit(**kwargs)


class SingleCardMenu(menus.Menu):
    """
    A menu that can go through different info of a card.
    """

    @classmethod
    def create_button_func(cls, view, *, doc):

        async def button_func(self, payload):
            await self.show_page(view)

        button_func.__doc__ = doc
        return button_func

    def __init__(self, card):
        super().__init__(check_embeds=True)
        self.card = card
        self.embed = discord.Embed(colour=discord.Colour.magenta())
        self.current_view = CardView.image
        buttons = [
            ("🗺️", CardView.image, "view the card image"),
            ("📘", CardView.text, "view a copy paste-able text format"),
            ("💸", CardView.prices, "view prices of the card"),
            ("🧾", CardView.legalities, "view the legalities of the card")
        ]

        for emoji, view, doc in buttons:
            self.add_button(menus.Button(emoji, self.create_button_func(view, doc=doc)))

    async def finalize(self, timed_out):
        try:
            await self.message.clear_reactions()
        except discord.HTTPException:
            pass

    @menus.button('*️⃣', position=menus.Last(0))
    async def show_help(self, payload):
        """shows this message"""
        embed = discord.Embed(title='Pages help', description='Hopefully this makes the buttons less confusing.',
                              colour=discord.Colour.purple())
        messages = []
        for (emoji, button) in self.buttons.items():
            messages.append(f'{emoji}: {button.action.__doc__}')

        embed.add_field(name='What do these reactions do?', value='\n'.join(messages), inline=False)
        await self.message.edit(content=None, embed=embed)

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=menus.Last(2))
    async def stop_pages(self, payload):
        """stops the pagination session."""
        self.stop()

    async def format_page(self, view):
        self.embed = view.value(self.card)
        return self.embed

    async def _get_kwargs_from_page(self, view):
        value = await self.format_page(view)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}

    async def show_page(self, view):
        self.current_view = view
        kwargs = await self._get_kwargs_from_page(view)
        await self.message.edit(**kwargs)

    async def send_initial_message(self, ctx, channel):
        kwargs = await self._get_kwargs_from_page(CardView.image)
        return await channel.send(**kwargs)


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
                    formatted.append(f"t:{split[1:]}")
            return " ".join(formatted)

        def is_convert(s):
            splits = s.split(" ")
            formatted = []
            for split in splits:
                if split.startswith("-") and len(split) > 2:
                    formatted.append(f"-is:{split[2:]}")
                elif len(split) > 1:
                    formatted.append(f"is:{split[1:]}")
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
                return f"c{s}"
            if s.startswith("=") and len(s) > 1:
                return f"c:{s[1:]}"
            return f"c:{s}"

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
             is_convert),

            ("is", "💡", "Card Types", "What type of card should it be? Seperate using ` ` and put `-` in front if "
             "you don't want that.", type_convert),

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
            await self.message.clear_reactions()
        except discord.HTTPException:
            pass

    @menus.button("❌", position=menus.First(1))
    async def stop_search(self, payload):
        """discard search"""
        self.stop()
        try:
            await self.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

    @menus.button("✅", position=menus.First(0))
    async def send_search(self, payload):
        """searches what you have set"""
        self.stop()
        try:
            await self.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
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
