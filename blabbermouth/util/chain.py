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
