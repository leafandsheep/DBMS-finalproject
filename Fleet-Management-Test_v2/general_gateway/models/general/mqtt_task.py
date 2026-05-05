import configparser
import os
import sys
from datetime import datetime

from general_gateway.apps.fleet.models.enum.task_type import TaskType
from general_gateway.models.enum.config_enum import ConfigEnum
from general_gateway.models.enum.project_name_enum import ProjectNameEnum
from general_gateway.models.enum.task_enum import TaskStatus


class MQTTTask:
    def __init__(
        self,
        task_type,
        task_sn: int = 0,
        gateway_sn: int = 0,
        task_id: str = "",
        task_status: TaskStatus = TaskStatus.CREATED,
        topic: str = "",
        content: dict = None,
        task_timeout: int = 1800,
        task_priority: int = 0,
        created_time: datetime = None,
        updated_time: datetime = None,
    ):
        if content is None:
            content = {}

        config = configparser.ConfigParser()
        config.read(ConfigEnum.FILE_NAME.value)
        project_name = ProjectNameEnum(config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_PROJECT_NAME.value])

        self.task_sn = task_sn
        self.gateway_sn = gateway_sn
        self.task_id = task_id
        self.task_status = task_status
        self.topic = topic
        self.content = content
        self.task_timeout = task_timeout
        self.task_priority = task_priority
        self.created_time = datetime.now().astimezone() if created_time is None else created_time
        self.updated_time = updated_time

        if isinstance(task_type, TaskType):
            self.task_type = task_type
        else:
            self.task_type = TaskType(task_type)

    def get_name(self):
        return sys._getframe(1).f_code.co_name

    def update_content(self, content):
        try:
            result = False
            self.content = content
            from general_gateway.common.db_utils import update_mqtt_task_content
            result = update_mqtt_task_content(self)

            return result

        except BaseException as n:
            print("Log Fail:", n)
            print(os.path.basename(__file__), self.get_name())

    def get_next_status(self):
        if self.task_status == TaskStatus.CREATED:
            self.task_status = TaskStatus.DISPATCHED
        elif self.task_status == TaskStatus.DISPATCHED:
            self.task_status = TaskStatus.DOING

        return self.task_status
