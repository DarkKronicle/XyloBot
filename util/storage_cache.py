"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Rapptz/RoboDanny: https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/cache.py

This is a really cool way to have caching enabled for different functions. I used some of the same logic that
Rapptz did in RoboDanny.

Tutorial on how this stuff works: https://realpython.com/primer-on-python-decorators/#caching-return-values
"""
import enum
from functools import wraps

from lru import LRU


class Strategy(enum.Enum):
    lru = 1
    raw = 2


def cache(maxsize=64, strategy=Strategy.lru):
    def decorator(func):
        if strategy is Strategy.lru:
            _internal_cache = LRU(maxsize)
        elif strategy is Strategy.raw:
            _internal_cache = {}
        else:
            _internal_cache = {}

        def create_key(*args, **kwargs):
            return args + tuple(kwargs.items())

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = create_key(args, kwargs)
            if key in _internal_cache:
                value = _internal_cache[key]
            else:
                value = func(*args, **kwargs)
                _internal_cache[key] = value

            if strategy is Strategy.raw:
                if len(_internal_cache) > maxsize:
                    to_del = list(_internal_cache)[0]
                    del _internal_cache[to_del]
            return value

        def _invalidate(*args, **kwargs):
            key = create_key(args, kwargs)
            if key in _internal_cache:
                del _internal_cache[key]
                return True
            return False

        def _invalidate_containing(key):
            for k in _internal_cache.keys():
                if key in k:
                    del _internal_cache[k]

        wrapper.cache = _internal_cache
        wrapper.invalidate = _invalidate
        wrapper.invalidate_containing = _invalidate_containing
        return wrapper
    return decorator
