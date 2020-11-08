from dataclasses import dataclass
from typing import List
from functools import reduce
from operator import xor

from common import Packet, StreamType


@dataclass()
class Carte(object):
    good: bool = False
    sfi: str = ''
    nmea: bytes = b''
    part: List[str] = None

class Doctor(object):
    def __init__(self):
        self.symbol450 = b'UdPbC\x00'

    def checkSum(self, *, src: bytes) -> int:
        return reduce(xor, src, 0)

    def getSFI(self, *, src: bytes) -> str:
        sfi = ''
        body = src.split(b'*')
        if self.checkSum(src=body[0]) == int(body[1], 16):
            sfi = ''
            for p in body[0].split(b','):
                item = p.split(b':')
                if item[0] == b's':
                    sfi = item[1].decode()
                    break
        return sfi

    def checkNMEA(self, *, src: bytes) -> bool:
        ok = False
        body = src.split(b'*')
        if len(body) == 2:
            if self.checkSum(src=body[0][1:]) == int(body[1][0:2], 16):
                ok = True
        else:
            ok = True
        return ok

    def toPart(selfself, *, src: bytes) -> List[str]:
        result = []
        body = src.split(b'*')
        if len(body) == 2:
            result.extend(body[0][1:].decode().split(','))
        else:
            result.extend(src[1:].decode().split(','))
        return result

    def physicalCheck(self, *, packet: Packet) -> Carte:
        carte = Carte()
        part = packet.stream.split(b'\\')
        if part[0] == self.symbol450:
            if packet.type == StreamType.Type450:
                sfi = self.getSFI(src=part[1])
                if sfi:
                    nmea = part[2][:-2]
                    if self.checkNMEA(src=nmea):
                        carte.sfi = sfi
                        carte.nmea = nmea
                        carte.part = self.toPart(src=nmea)
                        carte.good = True
        return carte
