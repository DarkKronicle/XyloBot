"""
A lot of code from here was used from Rapptz RoboDanny. RoboDanny is just amazing 10/10
https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py#L41

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
from abc import ABC

from discord.ext import menus, commands

from util.discord_util import *
import math

from util.paginator import Pages


class BotHelpPageSource(menus.ListPageSource, ABC):

    def __init__(self, help_command, cogs_commands):
        super().__init__(entries=sorted(cogs_commands.keys(), key=lambda c: c.qualified_name), per_page=6)
        self.help_command: Help = help_command
        self.cogs_commands: dict = cogs_commands

    # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py#L41
    def short_cog(self, cog: commands.Cog, cogs_commands):
        if cog.description:
            description = cog.description.split("\n", 1)[0] + "\n"
        else:
            description = "No information...\n"

        count = len(description)
        end_note = "+{} others"
        end_length = len(end_note)

        page = []

        for command in cogs_commands:
            name = f"`{command.name}`"
            name_count = len(name) + 1
            if name_count + count < 800:
                count += name_count
                page.append(name)
            else:
                if count + end_length + 1 > 800:
                    page.pop()
                break

        if len(page) == len(cogs_commands):
            return description + ' '.join(page)

        left = len(cogs_commands) - len(page)
        return description + ' '.join(page) + "\n" + end_note.format(str(left))

    async def format_page(self, menu, cogs):
        prefix = await self.help_command.context.bot.get_guild_prefix(self.help_command.context.guild.id)
        top = f"Prefixes you can use: `{prefix}`, `x>`\nUse `help [" \
              f"command]` for " \
              f"specific info on a command.\nUse `help [category]` for specific info in a category. \n" \
              f"*Use the reactions to look through commands*"

        embed = discord.Embed(title="Xylo Help - Categories", description=top, colour=discord.Colour.blue())

        for cog in cogs:
            cmds = self.cogs_commands.get(cog)
            if cmds:
                val = self.short_cog(cog, cmds)
                embed.add_field(name=cog.qualified_name, value=val, inline=True)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} categories)')

        pfp = self.help_command.context.bot.user.avatar_url
        embed.set_thumbnail(url=pfp)
        return embed


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group, commands, *, prefix):
        super().__init__(entries=commands, per_page=6)
        self.group = group
        self.prefix = prefix
        self.title = f'{self.group.qualified_name} Commands'
        self.description = self.group.description

    async def format_page(self, menu, commands):
        embed = discord.Embed(title=self.title, description=self.description, colour=discord.Colour.blue())

        for command in commands:
            signature = f'{command.qualified_name} {command.signature}'
            embed.add_field(name=signature, value=command.short_doc or 'No help given...', inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)')

        embed.set_footer(text=f'Use `help [command]` for more information on a specific command.')
        return embed


class HelpMenu(Pages):

    def __init__(self, source):
        super().__init__(source)


# Why is Rapptz so amazing? https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py
class Help(commands.HelpCommand):
    bot = None

    def __init__(self):
        super().__init__(command_attrs={
            'cooldown': commands.Cooldown(2, 9, commands.BucketType.user),
            'help': 'Shows help information for specific commands.'
        })

    def get_command_signature(self, command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'[{command.name}|{aliases}]'
            if parent:
                fmt = f'{parent} {fmt}'
            alias = fmt
        else:
            alias = command.name if not parent else f'{parent} {command.name}'
        return f'{alias} {command.signature}'

    async def send_bot_help(self, mapping, page=1):
        bot = self.context.bot
        entries = await self.filter_commands(bot.commands, sort=True)

        all_commands = {}
        for command in entries:
            if command.cog is None:
                continue
            try:
                all_commands[command.cog].append(command)
            except KeyError:
                all_commands[command.cog] = [command]

        menu = HelpMenu(BotHelpPageSource(self, all_commands))
        await menu.start(self.context)

    def common_command_formatting(self, embed_like, command):
        embed_like.title = self.get_command_signature(command)
        if command.description:
            embed_like.description = f'{command.description}\n\n{command.help}'
        else:
            embed_like.description = command.help or 'No help found...'

    async def send_command_help(self, command):
        # No pagination necessary for a single command.
        embed = discord.Embed(colour=discord.Colour.blue())
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        menu = HelpMenu(GroupHelpPageSource(cog, entries, prefix=self.clean_prefix))
        await menu.start(self.context)

    async def send_group_help(self, group):
        subcommands = group.commands
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True)
        if len(entries) == 0:
            return await self.send_command_help(group)

        source = GroupHelpPageSource(group, entries, prefix=self.clean_prefix)
        self.common_command_formatting(source, group)
        menu = HelpMenu(source)
        await menu.start(self.context)


def setup(bot):
    bot.add_cog(Help(bot=bot))
