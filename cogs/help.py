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

from util.discord_util import *
from storage import cache


class FullHelpMessage:

    def __init__(self, help_command, cogs_commands):
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

    async def send_help(self, page=1):
        top = f"Prefixes you can use: {cache.get_prefix(self.help_command.context.guild)}\nUse `help [command]` for " \
              f"specific info on a command.\nUse `help [category]` for specific info in a category.\nYou can also " \
              f"view other pages with `help page [num]`"

        embed = discord.Embed(title="Xylo Help - Categories", description=top, colour=discord.Colour.blue())
        start = page * 6 - 6
        end = page * 6 - 1
        page_cmds = self.cogs_commands.keys()[start:end]

        if len(page_cmds) == 0:
            self.help_command.context.send(f"Page number `{page}` is too big!", delete_after=15)
            return

        for cog in self.cogs_commands:
            cmds = self.cogs_commands.get(cog)
            if cmds:
                val = self.short_cog(cog, cmds)
                embed.add_field(name=cog.qualified_name, value=val, inline=True)

        pfp = self.help_command.context.bot.user.avatar_url
        embed.set_thumbnail(url=pfp)
        await self.help_command.context.send(embed=embed)


# Why is Rapptz so amazing? https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py
class Help(commands.HelpCommand):
    bot = None

    def __init__(self):
        super().__init__(command_attrs={
            'cooldown': commands.Cooldown(2, 9, commands.BucketType.user),
            'help': 'Shows help information for specific commands.'
        })

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

        command = FullHelpMessage(self, all_commands)
        await command.send_help(page)

    async def command_callback(self, ctx, *, command=None):
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        if command.split(' ')[0] == "page":
            if len(command.split(' ') != 2):
                await self.context.send("`help page <num>`")
                return
            try:
                num = int(command.split(' ')[1])
                mapping = self.get_bot_mapping()
                return await self.send_bot_help(mapping, page=num)
            except ValueError:
                await self.context.send("Incorrect page inputted!")
                return

        # Check if it's a cog
        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)

        maybe_coro = discord.utils.maybe_coroutine

        # If it's not a cog then it's a command.
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found

        if isinstance(cmd, commands.Group):
            return await self.send_group_help(cmd)
        else:
            return await self.send_command_help(cmd)


def setup(bot):
    bot.add_cog(Help(bot=bot))
