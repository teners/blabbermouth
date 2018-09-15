import functools
import inspect


class BrokenChain(Exception):
    pass


def check(value):
    if not value:
        raise BrokenChain()
    return value


def not_none(value):
    if value is None:
        raise BrokenChain()
    return value


def chained(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except BrokenChain:
            return None

    @functools.wraps(f)
    async def async_wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except BrokenChain:
            return None

    return async_wrapper if inspect.iscoroutinefunction(f) else wrapper
