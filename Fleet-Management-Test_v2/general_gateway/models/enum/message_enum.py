from enum import Enum, IntEnum


class MessageStatus(IntEnum):
    UNSENT = 0
    WAITING_FOR_ACK = 1
    FAILED = 2
    DONE = 3


class MessageType(IntEnum):
    REQUEST = 0
    RESPONSE = 1
    ACK = 2
    UNKNOWN = 3


class MessageDirection(Enum):
    FROM = "from"
    TO = "to"
