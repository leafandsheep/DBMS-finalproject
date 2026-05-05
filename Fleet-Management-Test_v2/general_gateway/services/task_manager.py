import os
import json
from datetime import datetime, timedelta
import time
import colorama
import redis

from general_gateway.common.datetime_utils import string_convert_to_date, data_plus_seconds
from general_gateway.common.db_utils import select_mqtt_tasks, update_mqtt_task_status_by_mqtt_task, \
    list_to_tuple_string, delete_mqtt_task_where_failed
from general_gateway.common.payload_format_util import read_task_content
from general_gateway.common.trace_error_util import trace_error, get_function_name
from general_gateway.models.enum.datetime_enum import DateTimeType
from general_gateway.models.enum.message_enum import MessageType
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.models.general.mqtt_task import MQTTTask
from general_gateway.apps.fleet.app_executor_fleet import AppExecutor
from general_gateway.models.mysql import MySQL
from apscheduler.schedulers.background import BackgroundScheduler
from termcolor import cprint


colorama.init()


class TaskManager:
    _instance = None
    _todo_task_dict = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._app_executor = AppExecutor()

        self.deal_timeout_task_scheduler = BackgroundScheduler()
        self.check_timeout_task_interval = 10

        self.deal_task_scheduler = BackgroundScheduler()
        self.re_fetch_task_interval_sec = 1

        self.is_deal_task_scheduler_starting = False
        
        # 20250516 楊皓宇
        redis_host = os.getenv('REDIS_HOST', 'iot_redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.r = redis.Redis(host=redis_host, port=redis_port)
        
        # 20240324 初始化任務為 0
        self.r.set('doing_task', '0'.encode('utf-8'))

        # 設定定期撈取指令
        # self.deal_cmd_scheduler = BackgroundScheduler()
        # self.re_fetch_cmd_interval_sec = 0.2

        # self.deal_timeout_cmd_scheduler = BackgroundScheduler()
        # self.check_timeout_cmd_interval = 20

    # 增加任務進任務列表
    def add_task_sn_to_task_list(self, task_sn, message_type: MessageType):
        print("\n Add Task!!! \n")
        self._todo_task_dict.update({task_sn: message_type.value})
        # print(self._todo_task_dict)

    # 從任務列表移除任務
    def remove_task_sn_from_task_list(self, task_sn):
        print("\n Remove Task!!! \n")
        self._todo_task_dict.pop(task_sn)
        # print(self._todo_task_dict)

    def start(self):
        self.deal_task_scheduler.add_job(
            self._deal_task, 'interval',
            seconds=self.re_fetch_task_interval_sec,
            id='_deal_task',
            coalesce=True
        )
        self.deal_timeout_task_scheduler.add_job(
            self._deal_timeout_task, 'interval',
            seconds=self.check_timeout_task_interval,
            id='_deal_timeout_task'
        )
        if not self.is_deal_task_scheduler_starting:
            self.deal_task_scheduler.start()
            self.deal_timeout_task_scheduler.start()
            self.is_deal_task_scheduler_starting = True
            
            # 初始化撈取指令函式
            # self.deal_cmd_scheduler.start()
            # 處理過期指令函式
            # self.deal_timeout_cmd_scheduler.start()
        
        # 新增定期撈取指令的函式
        # self.deal_cmd_scheduler.add_job(
        #     self._app_executor.app_pick_up_cmd , 'interval',
        #     seconds=self.re_fetch_cmd_interval_sec,
        #     id='_app_executor.',
        #     coalesce=True
        # )

        # 新增定期處理過期指令的函式
        # self.deal_timeout_cmd_scheduler.add_job(
        #     self._app_executor.app_deal_timeout_cmd, 'interval',
        #     seconds=self.check_timeout_cmd_interval,
        #     id='_deal_timeout_cmd'
        # )

    def _deal_timeout_task(self):
        try:
            # query_task_start = time.process_time()
            tasks = select_mqtt_tasks(task_status=TaskStatus.DOING)
            # query_task_end = time.process_time()
            # query_task = query_task_end - query_task_start
            # print("Query timeout task time: %f" % (query_task))
            if tasks:
                for task in tasks:
                    # deal_time_out_task_start = time.process_time()
                    elapsed_time = datetime.now() - task.updated_time
                    print(elapsed_time)
                    # 20240324 超過3分鐘未執行的任務即宣告任務失敗 by Mason
                    if(elapsed_time > timedelta(minutes=3)):
                        task.task_status = TaskStatus.FAILED
                        result = update_mqtt_task_status_by_mqtt_task(task)
                    # 20240326 移除 timeout 任務
                    if result:
                        delete_mqtt_task_where_failed()
                        print("\n\n Delete Timeout Task!!! \n\n")
                    # deal_time_out_task_end = time.process_time()
                    # deal_timeout_task = deal_time_out_task_end - deal_time_out_task_start
                    # print("Deal time out task: %f" % (deal_timeout_task))
        except BaseException as e:
            trace_error(e)
            return False

    def _deal_task(self):
        has_task_raw = self.r.get('has_task')
        doing_task_raw = self.r.get('doing_task')

        # 檢查得到的值是否為 None，並相對應解碼或設置為None
        has_task = has_task_raw.decode('utf-8') if has_task_raw is not None else None
        doing_task = doing_task_raw.decode('utf-8') if doing_task_raw is not None else None
        
        print("_deal_task: has_task", has_task)
        print("_deal_task: doing_task", doing_task)
        
        # 如果沒有任務或是正在執行任務則跳出
        if has_task == '0' or doing_task == '1':
            return 

        try:
            print("Into _deal_task!!\n\n")
            self.r.set('doing_task', '1'.encode('utf-8'))
            print("TaskManager TASK_DICT_KEY:", self._todo_task_dict)

            todo_task_list = list(self._todo_task_dict.keys())

            self.fetch_task_principle = {
                'where': {
                    'task_sn': list_to_tuple_string(todo_task_list)
                }
            }
            tasks = self.fetch_need_deal_tasks(**self.fetch_task_principle)

            if tasks:
                print(tasks)
                for task in tasks:
                    # _deal_task_start = time.process_time()
                    mqtt_task = MQTTTask(
                        task_sn=task.get('task_sn'),
                        gateway_sn=task.get('gateway_sn'),
                        task_id=task.get('task_id'),
                        task_type=task.get('task_type'),
                        task_status=TaskStatus(task.get('task_status')),
                        task_timeout=task.get('task_timeout'),
                        task_priority=task.get('task_priority'),
                        content=json.loads(task.get('content')),
                        created_time=string_convert_to_date(
                            str(task.get('created_time')),
                            datetime_type=DateTimeType.YMDHMS_FORMAT
                        ),
                    )

                    task_timeout = data_plus_seconds(
                        mqtt_task.created_time, mqtt_task.task_timeout)
                    now = datetime.now()

                    if now > task_timeout:
                        mqtt_task.task_status = TaskStatus.FAILED
                        update_mqtt_task_status_by_mqtt_task(mqtt_task=mqtt_task)
                    else:
                        message_type = MessageType(self._todo_task_dict.get(mqtt_task.task_sn))
                        mqtt_task = read_task_content(mqtt_task=mqtt_task)

                        self._app_executor.app_dispatch(mqtt_task, message_type)
                    # print(self._todo_task_dict)
                    self.remove_task_sn_from_task_list(mqtt_task.task_sn)

                    # _deal_task_end = time.process_time()
                    # _deal_task = _deal_task_end - _deal_task_start
                    # print("deal task time: %f" % (_deal_task))

            self.r.set('has_task', '0'.encode('utf-8'))
            self.r.set('doing_task', '0'.encode('utf-8'))

            print()
        except BaseException as e:
            trace_error(e)
            return False


    def fetch_need_deal_tasks(self, **principle):

        # TODO:experiment_3 part2
        # task_sn = int(R.get('task_sn').decode('utf-8'))
        # start_time = datetime.now()

        results = None
        try:
            fetch_deal_task_start = time.process_time()
            if principle:
                sql = "SELECT * FROM `mqtt_task` WHERE "
                sql_order = None
                sql_end = None
                for key in principle.keys():
                    if key == "limit":
                        key_value = principle[key]
                        sql_end = " limit {}".format(key_value)
                    elif key == "order by":
                        key_value = principle[key]
                        if type(key_value) == dict:
                            order_dict = principle[key].items()
                            for tuple_element in order_dict:
                                sql_order = " order by `{}` {} ".format(
                                    tuple_element[0], tuple_element[1])
                        else:
                            sql_order = " order by `{}`".format(key_value)
                    elif key == "where":
                        condition = principle[key]
                        i = 0
                        for condition_key in condition.keys():
                            i += 1
                            condition_key_value = condition[condition_key]

                            # if type(condition_key_value) == tuple:
                            if condition_key == "task_sn":
                                sql += " `{}` IN {}".format(condition_key,
                                                            condition_key_value)
                            else:
                                if condition_key == "created_time":
                                    sql += " `{}` > '{}'".format(
                                        condition_key, condition_key_value)
                                else:
                                    sql += " `{}` = '{}'".format(
                                        condition_key, condition_key_value)
                            if i != len(condition):
                                sql += " AND "

                if sql_order:
                    sql += sql_order
                if sql_end:
                    sql += sql_end
            else:
                sql = (
                    "SELECT * FROM `mqtt_task` "
                    "WHERE `task_status` IN (1) order by `created_time` ASC limit 1 "
                )

            db = MySQL()
            cprint("TaskManager:" + get_function_name(), "magenta")
            # print("fetch_need_deal_tasks: sql:", sql)
            results = db.query(sql)

            # end_time = datetime.now()
            # spend_time = end_time - start_time
            # print("撈取任務所花時間", spend_time)
            # insert_experiment_log(task_sn=task_sn, type_sn=2, spend_time=spend_time)

            db.close()
        except Exception as e:
            trace_error(e)
        finally:
            if results:
                print("-" * 10)
                print("Fetch:")
                # print(results)
                # print("-" * 10)
                # fetch_deal_task_end = time.process_time()
                # print("fetch need deal tasks time: %f" % (fetch_deal_task_end - fetch_deal_task_start))
            return results
