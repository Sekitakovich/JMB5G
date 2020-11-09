from dataclasses import dataclass
from enum import IntEnum
from datetime import datetime as dt


class StreamType(IntEnum):
    NAKED = 0
    Type450 = 1


@dataclass()
class Channel(object):
    name: str
    ipv4: str
    port: int
    type: StreamType


@dataclass()
class Packet(object):
    stream: bytes
    type: StreamType
    name: str
    sender: str
    counter: int


@dataclass()
class News(object):
    sfi: str
    body: bytes
    at: dt


