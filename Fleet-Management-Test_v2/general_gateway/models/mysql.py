import configparser

import pymysql.cursors

from general_gateway.models.enum.config_enum import ConfigEnum


class MySQL:
    def __init__(self):
        super(MySQL, self).__init__()
        config = configparser.ConfigParser()
        config.read(ConfigEnum.FILE_NAME.value)

        self.connection = pymysql.connect(
            host=config[ConfigEnum.DB.value][ConfigEnum.DB_HOST.value],
            user=config[ConfigEnum.DB.value][ConfigEnum.DB_USER.value],
            password=config[ConfigEnum.DB.value][ConfigEnum.DB_PASSWORD.value],
            db=config[ConfigEnum.DB.value][ConfigEnum.DB_DATABASE.value],
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
