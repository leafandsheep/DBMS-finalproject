import os
import socket
import time
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import redis

REDIS = redis.Redis(host='127.0.0.1', port=6379, db=1)
ReaderHashKey = "User"
ReaderAntenna1 = ReaderHashKey + "_RFID1"
ReaderAntenna1_2 = ReaderHashKey + "_RFID1_2"
ReaderAntenna2 = ReaderHashKey + "_RFID2"


def redis_set_value_by_hash_name_and_id(hash_name=None, \
                                        hash_id=None, value=None):
    if hash_name is None or hash_id is None:
        return None
    REDIS.hset(hash_name, hash_id, value)


class RFIDReader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RFIDReader, cls).__new__(cls)
            cls._instance._is_started = False
        return cls._instance

    def __init__(self):
        if (self._is_started): return

        self.host = "192.168.7.2"
        self.port = 3177
        self.restart_at_time = None
        self.restart_program_sec = 5
        self.restart_program_scheduler = BackgroundScheduler()

    def start(self):
        if not self._is_started:
            try:
                socket_setting_result = self.socket_setting()
                socket_connect_result = self.socket_connect()

                if not socket_setting_result:
                    raise Exception("Socket Setting Fail")
                if not socket_connect_result:
                    raise Exception("Socket Connect Fail")

            except BaseException as e:
                print("Error: RFIDReader: start():", e)
            else:
                while True:
                    self.read_RFID_from_socket()
                    time.sleep(0.05)
            finally:
                print("Program Restart After ", self.restart_program_sec, " s")
                self.restart_at_time = datetime.now() + timedelta(seconds=self.restart_program_sec)
                self.restart_program_scheduler.add_job(
                    self.start, 'date', run_date=self.restart_at_time)
                self.restart_program_scheduler.start()
                self._is_started = True

    def socket_setting(self):
        print("-" * 10)
        print("Socket Setting!")
        result = False
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = True
            print("Socket Setting END!")
            print("-" * 10)
        except Exception as e:
            print("Error: ")
        finally:
            return result

    def socket_connect(self):
        print("-" * 10)
        print("Socket Connect!")
        result = False
        try:
            self.s.connect((self.host, self.port))
            result = True
            print("Connect END!")
            print("-" * 10)
        except BaseException as e:
            print("Error: RFIDReader: socket_connect: ", e)
            raise Exception("123")
        finally:
            return result

    def read_RFID_from_socket(self):
        try:
            start_time = time.time()
            print("-------------------------")

            # if self.is_inventory:
            # 以前專題生寫的
            socket_data = self.s.recv(10000)

            # XML解析後 -> REDIS
            position_front = socket_data.decode().find(
                '<?xml version="1.0" encoding="UTF-8"?>')
            position_end = socket_data.decode().rfind('</inventory>')

            if (socket_data.decode().find('ADVANNET') == 0):
                socket_data.decode().find('<?xml version="1.0" encoding="UTF-8"?>')
                socket_data.decode()
                find_data = socket_data[position_front:position_end + 12]
                find_data.decode().replace('\n', '').replace('\t', '').replace('\r', '')
                if (find_data.decode().rfind('<?xml version="1.0" encoding="UTF-8"?>') == 0):
                    if (find_data.decode().endswith('</inventory>')):
                        root = ET.fromstring(find_data)
                        RSSI = 0
                        for ANTENNA in root.iter('prop'):
                            ANTENNA_data = [14]
                            ANTENNA_data = ANTENNA.text

                            if "RSSI" in ANTENNA_data:
                                RSSI = ANTENNA_data.split(":")[1]
                            else:
                                pass
                            if (ANTENNA_data.rfind('ANTENNA_PORT') == 0):
                                for node in root.iter('hexepc'):
                                    print("node:", node.text)
                                    print("RSSI:", RSSI)
                                    if (ANTENNA_data == 'ANTENNA_PORT:1'):
                                        redis_set_value_by_hash_name_and_id(
                                           hash_name=ReaderAntenna1_2, hash_id=node.text, value=RSSI)
                                        redis_set_value_by_hash_name_and_id(
                                            hash_name=ReaderAntenna1, hash_id=node.text, value=RSSI)
                                        print(ReaderAntenna1,
                                              " :", node.text)
                                    if (ANTENNA_data == 'ANTENNA_PORT:2'):
                                        redis_set_value_by_hash_name_and_id(
                                            hash_name=ReaderAntenna2, hash_id=node.text, value=RSSI)
                                        print(ReaderAntenna2,
                                              " :", node.text)
            print("start time:", start_time, ", seconds:", time.time()-start_time)
        except BaseException as e:
            print("Log Fail:", e)



if __name__ == '__main__':
    reader = RFIDReader()
    reader.start()
