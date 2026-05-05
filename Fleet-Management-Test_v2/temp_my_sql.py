# encoding=utf-8
# ! /usr/bin/python
import pymysql.cursors

ROLE = "Gateway"
# ROLE = "Server"


class MySQL:
    def __init__(self):
        super(MySQL, self).__init__()

        from setting import ROLE

        from config_loader import load_config
        cfg = load_config()

        if ROLE == "Gateway":
            DB_CONFIG = {
                'host': cfg.get('MYSQL_HOST'),
                'port': cfg.get('MYSQL_PORT'),
                'user': cfg.get('MYSQL_USER'),
                'password': cfg.get('MYSQL_PASSWORD'),
                'db': cfg.get('DB_NAME')
            }
        elif ROLE == "Server":
            DB_CONFIG = {
                'host': cfg.get('MYSQL_HOST'),
                'port': cfg.get('MYSQL_PORT'),
                'user': cfg.get('MYSQL_USER'),
                'password': cfg.get('MYSQL_PASSWORD'),
                'db': cfg.get('DB_NAME')
            }
        else:
            DB_CONFIG = {
                'host': cfg.get('MYSQL_HOST'),
                'port': cfg.get('MYSQL_PORT'),
                'user': cfg.get('MYSQL_USER'),
                'password': cfg.get('MYSQL_PASSWORD'),
                'db': cfg.get('DB_NAME')
            }

        self.connection = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def connect(self, host, user, password, db):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def reconnect(self, DB_CONFIG):
        self.connection = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def execute(self, sql):
        connection = self.connection
        cursor = connection.cursor()
        result = cursor.execute(sql)
        connection.commit()
        response = {"result": result, "sn": cursor.lastrowid}

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


class MySQL2:
    def __init__(self):
        super(MySQL2, self).__init__()
        
        from config_loader import load_config
        cfg = load_config()
        DB_CONFIG = {
            'host': cfg.get('MYSQL_HOST'),
            'port': cfg.get('MYSQL_PORT'),
            'user': cfg.get('MYSQL_USER'),
            'password': cfg.get('MYSQL_PASSWORD'),
            'db': cfg.get('DB_NAME')
        }

        self.connection = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def connect(self, host, user, password, db):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def reconnect(self, DB_CONFIG):
        self.connection = pymysql.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def execute(self, sql):
        connection = self.connection
        cursor = connection.cursor()
        result = cursor.execute(sql)
        connection.commit()
        response = {
            "result": result,
            "row_count": cursor.rowcount,
            "last_row_id": cursor.lastrowid,
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
