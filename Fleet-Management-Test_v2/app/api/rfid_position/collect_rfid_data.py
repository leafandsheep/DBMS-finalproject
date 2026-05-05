import os
import sys
import time
import smbus
import numpy as np
import pymysql.cursors
import redis

from imusensor.MPU9250 import MPU9250
from typing import Optional

REDIS = redis.Redis(host='127.0.0.1', port=6379, db=1)
ReaderHashKey = "User"
READER_ANTENNA_1 = ReaderHashKey + "_RFID1"
READER_ANTENNA_2 = ReaderHashKey + "_RFID2"


class MySQL:
    def __init__(self):
        super(MySQL, self).__init__()

        self.connection = pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="eS414o6kdd",
            db="indoor_position",
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )

    def connect(self, host, user, password, db):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )

    def reconnect(self, DB_CONFIG):
        self.connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute(self, sql):
        connection = self.connection
        cursor = connection.cursor()
        result = cursor.execute(sql)
        connection.commit()
        response = {
            'result': result,
            'sn': cursor.lastrowid
        }

        return response

    def query(self, state):
        connection = self.connection
        with connection.cursor() as cursor:
            cursor.execute(state)
            result = cursor.fetchall()

        return result

    def ping(self):
        self.connection.ping(reconnect=True)

    def close(self):
        self.connection.close()


def redis_get_scanned_RFID_tags(rfid_reader):
    key_dict = REDIS.hgetall(rfid_reader)
    print(key_dict)

    key_dict = {k.decode('utf-8'): int(v.decode('utf-8')) for k, v in key_dict.items()}

    print("key_dict:", key_dict)

    return key_dict


def redis_truncate(rfid_reader):
    REDIS.delete(rfid_reader)


def main():
    try:
        while(True):

            left_rfid_dict = str(redis_get_scanned_RFID_tags(READER_ANTENNA_1))
            right_rfid_dict = str(redis_get_scanned_RFID_tags(READER_ANTENNA_2))
            
            sql = "INSERT INTO `rfid_data_collection` (" \
                "`left_rfid`, `right_rfid`) VALUES (" \
                "\"{0}\", \"{1}\"" \
                ")".format(
                    left_rfid_dict, right_rfid_dict
                )
            print("sql:", sql)

            redis_truncate(READER_ANTENNA_1)
            redis_truncate(READER_ANTENNA_2)
            
                
            dbh = MySQL()
            result = dbh.execute(sql)
            dbh.close()
            time.sleep(0.5)
    
        redis_truncate(READER_ANTENNA_1)
        redis_truncate(READER_ANTENNA_2)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    redis_truncate(READER_ANTENNA_1)
    redis_truncate(READER_ANTENNA_2)

    main()
