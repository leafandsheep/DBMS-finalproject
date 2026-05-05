from enum import Enum


class ConfigEnum(Enum):
    FILE_NAME = 'general_gateway.ini'
    BASIC = 'basic'
    BASIC_BROKER_HOST = 'basic_broker_host'
    BASIC_SERVER_ID = 'basic_server_id'
    BASIC_GATEWAY_ID = 'basic_gateway_id'
    BASIC_ROLE = 'basic_role'
    BASIC_PROJECT_NAME = 'basic_project_name'

    DB = 'db'
    DB_HOST = 'db_host'
    DB_USER = 'db_user'
    DB_PASSWORD = 'db_password'
    DB_DATABASE = 'db_database'

    CUSTOM = 'custom'


