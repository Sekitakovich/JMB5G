from typing import Dict, List
from threading import Thread, Event, Lock
from queue import Queue, Empty
import time
from datetime import datetime as dt
from loguru import logger

from common import Channel, Packet, News, StreamType
from doctor import Doctor
from antenna import Antenna


class Main(object):
    '''
    JMB 5th generation
    '''

    def __init__(self):
        self.stock: Dict[str, News] = {}
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
                for symbol, body in self.stock.items():
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
                    logger.debug(carte.part)
                    nmea = carte.nmea
                    item = carte.part
                    name = item[0]
                    with self.locker:
                        '''
                        特別な処理・変換等が必要な場合ここで行う
                        '''
                        self.stock[name] = News(body=nmea, sfi=carte.sfi, at=dt.now())

        self.endWhistle.set()
        for m in self.listner:
            m.join()
            logger.debug('%s was joined' % (m.name))
        # reporter.join()


if __name__ == '__main__':
    def main():
        M = Main()
        M.dispose()

        for k, v in M.stock.items():
            print('%s = %s' % (k, v))


    main()
