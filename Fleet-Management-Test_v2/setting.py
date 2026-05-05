# setting.py
import os
from config_loader import load_config

cfg = load_config()

ROLE = cfg.get('ROLE')
RUN_ENV = cfg.get('RUN_ENV', 'flask')
SERVER_ID = cfg.get('SERVER_ID')
GATEWAY_ID = cfg.get('GATEWAY_ID')
GATEWAY_SN = cfg.get('GATEWAY_SN')
BROKER_HOST = cfg.get('BROKER_HOST')
DELIVER_WAY = cfg.get('DELIVER_WAY')

# 資料庫設定
DB_CONFIG = {
    'host': cfg.get('MYSQL_HOST'),
    'port': cfg.get('MYSQL_PORT'),
    'user': cfg.get('MYSQL_USER'),
    'password': cfg.get('MYSQL_PASSWORD'),
    'db': cfg.get('DB_NAME')
}