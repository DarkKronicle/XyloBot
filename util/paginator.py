"""
A lot of code from here was used from Rapptz RoboDanny. RoboDanny is just amazing 10/10
# https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/cogs/utils/paginator.py#L6:1

The MIT License (MIT)

Copyright (c) 2020 Rapptz,
              2020 DarkKronicle

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
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
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass


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
