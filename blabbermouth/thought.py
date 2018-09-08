import enum

import attr


class Type(enum.Enum):
    TEXT = enum.auto()
    SPEECH = enum.auto()


@attr.s(slots=True, frozen=True)
class _Thought:
    thought_type = attr.ib()
    payload = attr.ib()


def text(payload):
    return _Thought(thought_type=Type.TEXT, payload=payload)


def speech(payload):
    return _Thought(thought_type=Type.SPEECH, payload=payload)
