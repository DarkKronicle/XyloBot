"""
A lot of code from here was used from Rapptz RoboDanny. RoboDanny is just amazing 10/10
# https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/cogs/utils/paginator.py#L6:1

The MPL-v2

Copyright (c) 2020 Rapptz,
              2020 DarkKronicle
"""
import asyncio
import discord
from discord.ext.commands import Paginator as CommandPaginator
from discord.ext import menus


class Pages(menus.MenuPages):

    def __init__(self, source, **kwargs):
        super().__init__(source=source, check_embeds=True, **kwargs)

    async def finalize(self, timed_out):
        try:
            await self.message.clear_reactions()
        except discord.HTTPException:
            pass

    @menus.button('*️⃣', position=menus.Last(5))
    async def show_help(self, payload):
        """shows this message"""
        embed = discord.Embed(title='Pages help', description='Hopefully this makes the buttons less confusing.', colour=discord.Colour.purple())
        messages = []
        for (emoji, button) in self.buttons.items():
            messages.append(f'{emoji}: {button.action.__doc__}')

        embed.add_field(name='What do these reactions do?', value='\n'.join(messages), inline=False)
        await self.message.edit(content=None, embed=embed)


class TextPageSource(menus.ListPageSource):
    def __init__(self, text, *, prefix='```', suffix='```', max_size=2000):
        pages = CommandPaginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split('\n'):
            pages.add_line(line)

        super().__init__(entries=pages, per_page=1)

    async def format_page(self, menu, content):
        maximum = self.get_max_pages()
        if maximum > 1:
            return f'{content}\nPage {menu.current_page + 1}/{maximum}'
        return content


class SimplePageSource(menus.ListPageSource):

    def __init__(self, entries, *, per_page=15):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu, entries):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f"**{index + 1}.** {entry}")

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries.)"
            menu.embed.set_footer(text=footer)

        menu.embed.description = '\n'.join(pages)
        return menu.embed


class SimplePages(Pages):

    def __init__(self, entries, *, per_page=15, embed=discord.Embed(colour=discord.Colour.purple())):
        super().__init__(SimplePageSource(entries, per_page=per_page))
        self.embed = embed
        self.entries = entries
