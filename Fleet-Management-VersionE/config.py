import logging
import os
from logging.handlers import RotatingFileHandler

from config_loader import load_config

cfg = load_config()


def cfg_value(key, default=None):
    return os.getenv(key, cfg.get(key, default))


class BasicConfig(object):
    SECRET_KEY = cfg_value('SECRET_KEY', 'warehouse-demo-secret')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False

    @staticmethod
    def init_app(app):
        handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        app.logger.addHandler(handler)


class DevelopmentConfig(BasicConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{cfg_value('MYSQL_USER')}:{cfg_value('MYSQL_PASSWORD')}"
        f"@{cfg_value('MYSQL_HOST')}:{cfg_value('MYSQL_PORT')}/{cfg_value('DB_NAME')}"
    )


class ProductionConfig(BasicConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{cfg_value('MYSQL_USER')}:{cfg_value('MYSQL_PASSWORD')}"
        f"@{cfg_value('MYSQL_HOST')}:{cfg_value('MYSQL_PORT')}/{cfg_value('DB_NAME')}"
    )


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
