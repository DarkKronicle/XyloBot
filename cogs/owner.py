"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import asyncio
import importlib
import os
import re
import subprocess
import sys

import psutil
from discord.ext import commands

from util.context import Context
from xylo_bot import XyloBot


# Most functionality taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L81
# Under MPL-2.0

from pathlib import Path, PosixPath


class DisplayablePath(object):
    display_filename_prefix_middle = '├──'
    display_filename_prefix_last = '└──'
    display_parent_prefix_middle = '    '
    display_parent_prefix_last = '│   '

    def __init__(self, path, parent_path, is_last):
        self.path = Path(str(path))
        self.parent = parent_path
        self.is_last = is_last
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0

    @property
    def displayname(self):
        if self.path.is_dir():
            return self.path.name + '/'
        return self.path.name

    @classmethod
    def make_tree(cls, root, parent=None, is_last=False, criteria=None):
        root = Path(str(root))
        criteria = criteria or cls._default_criteria

        displayable_root = cls(root, parent, is_last)
        yield displayable_root

        children = sorted(list(path
                               for path in root.iterdir()
                               if criteria(path)),
                          key=lambda s: str(s).lower())
        count = 1
        for path in children:
            is_last = count == len(children)
            if path.is_dir():
                yield from cls.make_tree(path,
                                         parent=displayable_root,
                                         is_last=is_last,
                                         criteria=criteria)
            else:
                yield cls(path, displayable_root, is_last)
            count += 1

    @classmethod
    def _default_criteria(cls, path):
        return True

    def displayable(self):
        if self.parent is None:
            return self.displayname

        _filename_prefix = (self.display_filename_prefix_last
                            if self.is_last
                            else self.display_filename_prefix_middle)

        parts = ['{!s} {!s}'.format(_filename_prefix,
                                    self.displayname)]

        parent = self.parent
        while parent and parent.parent is not None:
            parts.append(self.display_parent_prefix_middle
                         if parent.is_last
                         else self.display_parent_prefix_last)
            parent = parent.parent

        return ''.join(reversed(parts))


def get_dir_tree(start_path, *, blocked_extensions=None, blocked_directories=None, blocked_files=None, pretty=True):
    if blocked_files is None:
        blocked_files = []
    if blocked_directories is None:
        blocked_directories = []
    if blocked_extensions is None:
        blocked_extensions = []

    def criteria(path):
        if path.name in blocked_directories:
            return False
        ext = os.path.splitext(path.name)
        if path.name in blocked_files:
            return False
        if len(ext) > 0 and ext in blocked_extensions:
            return False
        return True

    paths = DisplayablePath.make_tree(start_path, criteria=criteria)
    full_start = str(Path(start_path).resolve())
    message = ""
    for path in paths:
        if pretty:
            message = message + path.displayable() + "\n"
        else:
            p = str(path.path.resolve()).replace(full_start, "", 1)
            message = message + p + "\n"
    return message


class Owner(commands.Cog):
    """
    Class for the owner to manage the bot.
    """

    def __init__(self, bot):
        self.bot: XyloBot = bot

    async def cog_check(self, ctx: Context):
        return await self.bot.is_owner(ctx.author)

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

    _GIT_PULL_REGEX = re.compile(r'\s*(?P<filename>.+?)\s*\|\s*[0-9]+\s*[+-]+')

    def find_modules_from_git(self, output):
        files = self._GIT_PULL_REGEX.findall(output)
        ret = []
        for file in files:
            root, ext = os.path.splitext(file)
            if ext != '.py':
                continue

            if root.startswith('cogs/'):
                if root.count("/") > 1:
                    ret.append((True, root.replace('/', '.')))
                else:
                    ret.append((False, root.replace('/', '.')))
            elif root.count('/') > 0:
                # We want to make sure it's in a sub directory. If it isn't then we don't need to worry about it.
                ret.append((True, root.replace('/', '.')))

        # For reload order, the submodules should be reloaded first
        ret.sort(reverse=True)
        return ret

    def reload_or_load_extension(self, module):
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionNotLoaded:
            self.bot.load_extension(module)

    @commands.command(name="*unload", hidden=True)
    async def unload(self, ctx: Context, *, module):
        if module is None:
            return await ctx.send("Specify a module")
        try:
            self.bot.unload_extension("cogs." + module)
        except commands.ExtensionError as e:
            await ctx.send(e)
        else:
            await ctx.send("Unloaded!")

    @commands.command(name="*load", hidden=True)
    async def load(self, ctx: Context, *, module):
        if module is None:
            return await ctx.send("Specify a module")
        try:
            self.bot.load_extension("cogs." + module)
        except commands.ExtensionError as e:
            await ctx.send(e)
        else:
            await ctx.send("Loaded!")

    @commands.group(name='*reload', hidden=True, invoke_without_command=True)
    async def _reload(self, ctx: Context, *, module):
        try:
            self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('Reloaded!')

    @_reload.command(name="restart", hidden=True)
    async def restart(self, ctx: Context):
        async with ctx.typing():
            stdout, stderr = await self.run_process('git pull')
        await ctx.send(f"{stdout}\n\n{stderr}")
        try:
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            await ctx.send(e)

        python = sys.executable
        os.execl(python, python, *sys.argv)

    @_reload.command(name='all', hidden=True)
    async def _reload_all(self, ctx: Context):
        """Reloads all modules, while pulling from git."""

        async with ctx.typing():
            stdout, stderr = await self.run_process('git pull')

        # progress and stuff is redirected to stderr in git pull
        # however, things like "fast forward" and files
        # along with the text "already up-to-date" are in stdout

        if stdout.startswith('Already up to date.'):
            return await ctx.send(stdout)

        modules = self.find_modules_from_git(stdout)
        if len(modules) is None:
            return await ctx.send("No modules to update.")
        mods_text = '\n'.join(f'{index}. `{module}`' for index, (_, module) in enumerate(modules, start=1))
        prompt_text = f'This will update the following modules, are you sure?\n{mods_text}'
        confirm = await ctx.prompt(prompt_text)
        if not confirm:
            return await ctx.send('Aborting.')

        statuses = []
        for is_submodule, module in modules:
            if is_submodule:
                try:
                    actual_module = sys.modules[module]
                except KeyError:
                    statuses.append(("⛔", module))
                else:
                    try:
                        importlib.reload(actual_module)
                    except Exception:
                        statuses.append(("❌", module))
                    else:
                        statuses.append(("✅", module))
            else:
                try:
                    self.reload_or_load_extension(module)
                except commands.ExtensionError:
                    statuses.append(("❌", module))
                else:
                    statuses.append(("✅", module))

        await ctx.send('\n'.join(f'{status}: `{module}`' for status, module in statuses))

    @commands.command(name="*list", hidden=True)
    async def _list(self, ctx: Context, *start_path):
        if start_path is None or len(start_path) == 0:
            start_path = "."
        else:
            start_path = ' '.join(start_path)

        dir_blacklist = ("pycache", ".git", "hooks", "refs", "objects", "__pycache__", "venv")
        ext_blacklist = (".pyc", ".cfg")
        # https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python

        message = "```\n" + get_dir_tree(start_path, blocked_directories=dir_blacklist, blocked_extensions=ext_blacklist)
        if len(message) > 1990:
            message = message[:1990]
        message = message + "```"
        await ctx.send(message)

    @commands.command(name="*plist", hidden=True)
    async def plist(self, ctx: Context, *start_path):
        if start_path is None or len(start_path) == 0:
            start_path = "."
        else:
            start_path = ' '.join(start_path)

        dir_blacklist = ("pycache", ".git", "hooks", "refs", "objects", "__pycache__", "venv")
        ext_blacklist = (".pyc", ".cfg")
        # https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python

        message = "```\n" + get_dir_tree(start_path, blocked_directories=dir_blacklist,
                                         blocked_extensions=ext_blacklist, pretty=False)
        if len(message) > 1990:
            message = message[:1990]
        message = message + "```"
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Owner(bot))
