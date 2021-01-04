from enum import IntEnum


class Kind(IntEnum):
    BUILTIN = 1
    CUSTOM = 2


class State(IntEnum):
    PENDING = 1
    BUILDING = 2
    SUCCESS = 3
    FAILED = 4
