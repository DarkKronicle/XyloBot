import asyncio

import discord
from discord.ext import menus
import enum

from scrython.cards.cards_object import CardsObject

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
    if card.type_line() == 'Creature':
        pt = "({}/{})".format(card.power(), card.toughness())
    else:
        pt = ""

    if card.cmc() == 0:
        mana_cost = ""
    else:
        mana_cost = card.mana_cost()

    description = """
    {cardname} {mana_cost}
    {type_line} -- {set_code} 
    {oracle_text} {power_toughness}
    *{rarity}*
    """.format(
        cardname=card.name(),
        mana_cost=mana_cost,
        type_line=card.type_line(),
        set_code=card.set_name(),
        rarity=card.rarity(),
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
    image = 0
    text = 1
    legalities = 2
    prices = 3


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
            q = menu.query[:20]
        else:
            q = menu.query + "..."
        embed.set_author(name=f"Search Results For: {q}")
        embed.colour = discord.Colour.magenta()
        menu.embed = embed
        return menu.embed

    async def format_card(self, menu, card):
        view = menu.view_type
        if view == CardView.image:
            embed = card_image_embed(card)
        elif view == CardView.text:
            embed = card_text_embed(card)
        elif view == CardView.legalities:
            embed = card_legal_embed(card)
        elif view == CardView.prices:
            embed = card_prices_embed(card)
        else:
            embed = card_image_embed(card)
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


class SingleCardSource(menus.ListPageSource):

    def __init__(self, card, *, per_page=1):
        self.card = card
        super().__init__(range(len(CardView)), per_page=per_page)

    async def format_page(self, menu, entries):
        view = CardView(entries[0])
        if view == CardView.image:
            embed = card_image_embed(self.card)
        elif view == CardView.text:
            embed = card_text_embed(self.card)
        elif view == CardView.legalities:
            embed = card_legal_embed(self.card)
        elif view == CardView.prices:
            embed = card_prices_embed(self.card)
        else:
            embed = card_image_embed(self.card)
        embed.set_footer(text=f"{embed.footer.text} - Showing type {menu.current_page + 1}/{len(self.entries)}")
        menu.embed = embed
        return menu.embed

    def is_paginating(self):
        # We always want buttons so that we can view card information.
        return True


class SingleCardMenu(Pages):
    """
        A menu that consists of two parts, the list of all cards, then the in depth card view on each.
        """

    def __init__(self, card):
        super().__init__(CardSearchSource(card))
        self.embed = discord.Embed(colour=discord.Colour.magenta())

    def _skip_double_triangle_buttons(self):
        # The way we are using the pages to go between different views would be really weird to skip to the beginning.
        return True
