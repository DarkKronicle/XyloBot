import asyncio

import discord
from discord.ext import menus

from util.paginator import Pages


class CardSearchSource(menus.ListPageSource):

    def __init__(self, entries, *, per_page=15):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu, entries):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f"**{index + 1}.** {entry.name()}")

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries.)"
            menu.embed.set_footer(text=footer)

        menu.embed.description = '\n'.join(pages)
        return menu.embed

    async def format_card(self, menu, card):
        menu.embed = card_embed(card)
        return menu.embed

    def is_paginating(self):
        # We always want buttons so that we can view card information.
        return True


class CardSearch(Pages):
    """
    A menu that consists of two parts, the list of all cards, then the in depth card view on each.
    """

    def __init__(self, entries, *, per_page=15):
        super().__init__(CardSearchSource(entries, per_page=per_page))
        self.embed = discord.Embed(colour=discord.Colour.magenta())
        self.entries = entries
        self.current_card = 0
        self.card_view = False

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
        self.embed.set_image(url=discord.Embed.Empty)
        await super().show_page(page_number)

    @menus.button('\N{INFORMATION SOURCE}\ufe0f', position=menus.Last(4))
    async def show_help(self, payload):
        """shows this message"""
        embed = discord.Embed(title='Paginator help', description='Hello! Welcome to the help page.')
        messages = []
        for (emoji, button) in self.buttons.items():
            messages.append(f'{emoji}: {button.action.__doc__}')

        embed.add_field(name='What are these reactions for?', value='\n'.join(messages), inline=False)
        embed.set_footer(text=f'We were on page {self.current_page + 1} before this message.')
        await self.message.edit(content=None, embed=embed)

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