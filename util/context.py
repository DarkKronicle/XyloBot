"""
This class was heavily based off of https://github.com/Rapptz/RoboDanny/blob/7cd472ca021e9e166959e91a7ff64036474ea46c/cogs/utils/context.py#L23:1
Rapptz is amazing.
The code above was released under MIT license.
"""

from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
