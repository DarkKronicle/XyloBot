"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import asyncio
import importlib
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import psutil
from discord.ext import commands

from util.context import Context
from util.file_management import DisplayablePath
from xylo_bot import XyloBot


# Most functionality taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L81
# Under MPL-2.0


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

        paths = DisplayablePath.make_tree(start_path,
                                          criteria=DisplayablePath.block_criteria(blocked_extensions=ext_blacklist,
                                                                                  blocked_directories=dir_blacklist))
        message = "```\n"
        for path in paths:
            message = message + path.displayable() + "\n"

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

        paths = DisplayablePath.make_tree(start_path, criteria=DisplayablePath.block_criteria(blocked_extensions=ext_blacklist, blocked_directories=dir_blacklist))
        full_start = str(Path(start_path).resolve())

        message = "```\n"
        for path in paths:
            p = str(path.path.resolve()).replace(full_start, "", 1)
            message = message + p + "\n"

        if len(message) > 1990:
            message = message[:1990]
        message = message + "```"
        await ctx.send(message)

    @commands.command(name="*randline", hidden=True)
    async def rand_line(self, ctx: Context):
        dir_blacklist = ("pycache", ".git", "hooks", "refs", "objects", "__pycache__", "venv", "assets")
        ext_blacklist = (".pyc", ".cfg")
        file_blacklist = ("configs.json", "owner.py", "requirements.txt", "LICENSE.txt")

        paths = []
        for p in DisplayablePath.make_tree(".", criteria=DisplayablePath.block_criteria(blocked_extensions=ext_blacklist, blocked_directories=dir_blacklist, blocked_files=file_blacklist)):
            paths.append(p.path)
        file_path = random.choice(paths)
        text = file_path.read_text()
        lines = text.split("\n")
        for l in lines.copy():
            if l == "":
                lines.remove(l)
        line = random.choice(lines)
        await ctx.send(f"```{line}```")


def setup(bot):
    bot.add_cog(Owner(bot))
