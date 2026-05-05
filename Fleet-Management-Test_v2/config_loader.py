# config_loader.py
import os
import configparser


def load_config():
    CONFIG_FILE = os.getenv("CONFIG_FILE", "./default_config.ini")
    cp = configparser.ConfigParser()
    cp.read(CONFIG_FILE, encoding='utf-8')
    return cp['default']
