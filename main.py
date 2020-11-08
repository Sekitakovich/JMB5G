from typing import Dict, List
from threading import Thread, Event, Lock
from queue import Queue, Empty
import socket
from contextlib import closing
import time
from datetime import datetime as dt
from loguru import logger

from common import Channel, Packet, NmeaShelf, StreamType
from doctor import Doctor


class Antenna(Thread):
    def __init__(self, *, channel: Channel, entryQueue: Queue, endWhistle: Event):
        super().__init__()
        self.name = channel.name
        self.daemon = True

        self.bufferSize = 4096
        self.timeLimit = 5
        self.counter = 0

        self.channel = channel
        self.entryQueye = entryQueue
        self.endWhistle = endWhistle
        self.running = True

    def director(self):
        self.endWhistle.wait()
        self.endWhistle.clear()
        self.running = False
        # logger.debug('[%s] Catch endwhistle' % (self.name))

    def run(self) -> None:
        director = Thread(target=self.director, daemon=True)
        director.start()

        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                            socket.inet_aton(self.channel.ipv4) + socket.inet_aton('0.0.0.0'))
            sock.settimeout(self.timeLimit)
            sock.bind(('', self.channel.port))
            while self.running:
                try:
                    stream, ipv4 = sock.recvfrom(self.bufferSize)
                except (socket.timeout) as e:
                    logger.warning('[%s] %s' % (self.name, e))
                    pass
                except (socket.error) as e:
                    logger.error('[%s] %s' % (self.name, e))
                    self.running = False
                else:
                    packet = Packet(stream=stream, name=self.name, sender=ipv4[0], counter=self.counter,
                                    type=self.channel.type)
                    self.entryQueye.put(packet)
                    self.counter += 1
        logger.debug('Sir yes sir!')
        director.join()


class Main(object):
    '''
    JMB 5th generation
    '''

    def __init__(self):
        self.shelf: Dict[str, NmeaShelf] = {}
        self.entryQueue = Queue()
        self.endWhistle = Event()
        self.locker = Lock()
        self.doctor = Doctor()

        self.channel: List[Channel] = [
            Channel(ipv4='239.192.0.1', port=60001, name='GPS1', type=StreamType.Type450),
            Channel(ipv4='239.192.0.2', port=60002, name='GPS2', type=StreamType.Type450),
            Channel(ipv4='239.192.0.3', port=60003, name='Gyro', type=StreamType.Type450),
            Channel(ipv4='239.192.0.4', port=60004, name='Sonar', type=StreamType.Type450),
            Channel(ipv4='239.192.0.5', port=60005, name='Depth', type=StreamType.Type450),
            Channel(ipv4='239.192.0.6', port=60006, name='Weather', type=StreamType.Type450),
            Channel(ipv4='239.192.0.7', port=60007, name='AutoP', type=StreamType.Type450),
            Channel(ipv4='239.192.0.8', port=60008, name='AIS', type=StreamType.Type450),
        ]
        self.listner: List[Thread] = []

    def report(self):
        while True:
            time.sleep(1)
            with self.locker:
                for symbol, body in self.shelf.items():
                    print('%s = %s' % (symbol, body))

    def dispose(self):

        # reporter = Thread(target=self.report, daemon=True)
        # reporter.start()

        for c in self.channel:
            thread = Antenna(channel=c, entryQueue=self.entryQueue, endWhistle=self.endWhistle)
            thread.start()
            self.listner.append(thread)

        while True:
            try:
                packet = self.entryQueue.get(timeout=1)
            except (Empty) as e:
                pass
                # logger.warning(e)
            except (KeyboardInterrupt) as e:
                break
            else:
                carte = self.doctor.physicalCheck(packet=packet)
                if carte.good:
                    logger.debug(carte.nmea)
                    with self.locker:
                        nmea = carte.nmea
                        item = carte.part
                        symbol = item[0][1:]
                        self.shelf[symbol] = NmeaShelf(body=nmea, sfi=carte.sfi, at=dt.now())

        self.endWhistle.set()
        for m in self.listner:
            m.join()
            logger.debug('%s was joined' % (m.name))
        # reporter.join()


if __name__ == '__main__':
    def main():
        M = Main()
        M.dispose()

        for k, v in M.shelf.items():
            print('%s = %s' % (k, v))


    main()
