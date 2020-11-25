import asyncio

import discord
from discord.ext import menus

from util.mtg_deck import Deck, DeckCard
from util.mtg_pages import append_exists, color_from_card
from util.paginator import Pages


def card_image(card: DeckCard):
    description = append_exists("", Section=card.section, Mana=card.mana)
    embed = discord.Embed(
        description=description,
        colour=color_from_card(card)
    )
    curl = card.url or discord.Embed.Empty
    embed.set_author(name=card.raw_text, url=curl)
    url = card.image
    if url is not None:
        embed.set_image(url=str(url))
    return embed


class DeckSource(menus.ListPageSource):

    def __init__(self, deck, *, per_page=15):
        super().__init__(deck.cards, per_page=per_page)

    async def format_page(self, menu, entries):
        embed = discord.Embed(colour=discord.Colour.magenta())
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f"**{index + 1}.** {entry.raw_text}")

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries.)"
            embed.set_footer(text=footer)

        embed.description = '\n'.join(pages)
        embed.set_author(name=f"{menu.deck.name}")
        embed.colour = discord.Colour.green()
        menu.embed = embed
        return menu.embed

    async def format_card(self, menu, card):
        embed = discord.Embed(

        )
        embed.set_footer(text=f"{embed.footer.text} - Showing card {menu.current_card + 1}/{len(self.entries)}")
        menu.embed = embed
        return menu.embed

    def is_paginating(self):
        # We always want buttons so that we can view card information.
        return True


class DeckPages(Pages):
    """
    A menu that consists of two parts, the list of all cards, then the in depth card view on each.
    """

    def __init__(self, deck: Deck, *, per_page=15):
        super().__init__(DeckSource(deck, per_page=per_page))
        self.embed = discord.Embed(colour=discord.Colour.green())
        self.deck = deck
        self.current_card = 0
        self.card_view = False

    def _skip_singles(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None or max_pages <= 1:
            max_cards = len(self.deck.cards)
            if max_cards <= 1:
                return True
            return False
        else:
            return False

    def _skip_doubles(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None or max_pages <= 2:
            max_cards = len(self.deck.cards)
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
        max_cards = len(self.deck.cards)
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
        card = self.deck.cards[card_number]
        self.current_card = card_number
        kwargs = await self._get_kwargs_from_card(card)
        await self.message.edit(**kwargs)
