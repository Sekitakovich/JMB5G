import socket
from contextlib import closing
from threading import Thread, Event
from queue import Queue
from loguru import logger

from common import Channel, Packet

class Antenna(Thread):
    def __init__(self, *, channel: Channel, entryQueue: Queue, endWhistle: Event):
        super().__init__()
        self.name = channel.name
        self.daemon = True

        self.bufferSize = 4096
        self.timeLimit = 5
        self.counter = 0

        self.channel = channel
        self.entryQueue = entryQueue
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
                    self.entryQueue.put(packet)
                    self.counter += 1
        logger.debug('Sir yes sir!')
        director.join()


