import configparser

from general_gateway.models.enum.config_enum import ConfigEnum
from general_gateway.models.enum.project_name_enum import ProjectNameEnum
from general_gateway.services.doorkeeper import Doorkeeper
from general_gateway.services.task_manager import TaskManager


class GeneralGateway:
    _instance = None
    __config = None
    __doorkeeper = None
    __task_manager = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print(f"Creating new instance: {cls._instance}")
        return cls._instance

    def __init__(self):
        # 20240717 Original
        # self.__config = configparser.ConfigParser()
        # self.__doorkeeper = None
        # self.__task_manager = None
       if not GeneralGateway._initialized:  # 檢查是否已經初始化過
            self.__config = configparser.ConfigParser()
            self.__doorkeeper = None
            self.__task_manager = None
            self._initialized = True

    def start(self):
        if self.__doorkeeper is None:
            self.__doorkeeper = Doorkeeper()
            self.__doorkeeper.start()
        if self.__task_manager is None:
            self.__task_manager = TaskManager()
            self.__task_manager.start()
        return self

    def set_basic_config(self, broker_host, server_id, gateway_id, role, project_name: ProjectNameEnum):
        self.__config[ConfigEnum.BASIC.value] = {}
        self.__config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_BROKER_HOST.value] = broker_host
        self.__config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_SERVER_ID.value] = server_id
        self.__config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_GATEWAY_ID.value] = gateway_id
        self.__config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_ROLE.value] = role
        self.__config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_PROJECT_NAME.value] = project_name.value
        
        with open(ConfigEnum.FILE_NAME.value, 'w') as configfile:
            self.__config.write(configfile)

        return self

    def set_db_connection(self, host, user, password, db):
        self.__config[ConfigEnum.DB.value] = {}
        self.__config[ConfigEnum.DB.value][ConfigEnum.DB_HOST.value] = host
        self.__config[ConfigEnum.DB.value][ConfigEnum.DB_USER.value] = user
        self.__config[ConfigEnum.DB.value][ConfigEnum.DB_PASSWORD.value] = password
        self.__config[ConfigEnum.DB.value][ConfigEnum.DB_DATABASE.value] = db

        with open(ConfigEnum.FILE_NAME.value, 'w') as configfile:
            self.__config.write(configfile)
        return self

    def get_doorkeeper_connecting_status(self):
        return self.__doorkeeper.is_connecting_mqtt_broker

    def set_custom_config(self, keys, values):
        self.__config[ConfigEnum.CUSTOM.value] = {}
        for i, key in enumerate(keys):
            self.__config[ConfigEnum.CUSTOM.value][key] = str(values[i])

        with open(ConfigEnum.FILE_NAME.value, 'w') as configfile:
            self.__config.write(configfile)
        return self
