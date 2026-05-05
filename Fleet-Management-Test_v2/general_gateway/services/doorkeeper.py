import os
import configparser
import json
import logging
import random
import asyncio
import queue
import time
import uuid
import queue
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
import colorama
import paho.mqtt.client as mqtt
import redis
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from general_gateway.apps.fleet.models.enum.task_type import TaskType
from logging.handlers import RotatingFileHandler
from termcolor import cprint
from general_gateway.apps.fleet.db_fleet import update_mqtt_task_by_task_sn_and_gateway_sn, \
    delete_mqtt_task_from_can_not_do_task_list, select_mqtt_gateways
from general_gateway.common.db_utils import insert_mqtt_task, add_to_mqtt_message, \
    update_mqtt_message_status_by_message_id, delete_DONE_mqtt_message, select_mqtt_message_by_message_id, \
    update_mqtt_task_status_by_mqtt_task, delete_mqtt_task_where_terminated, \
    select_mqtt_tasks, record_message_transfer_time, delete_real_time_mqtt_message, insert_msg_send_receive, \
    update_msg_status_by_id, delete_FAILED_mqtt_message, maintain_mqtt_message_table, update_resend_times_by_message_id, \
    update_message_status_in_messsage_log, update_message_log, update_done_message_in_message_log, insert_app_message_log, select_message_from_message_log, \
    update_payload_and_timestamp_in_message_log, update_message_log_without_payload_timestamp, \
    update_done_message_in_message_log_only_timestamp, update_done_message_in_message_log_no_timestamp
from general_gateway.common.mqtt_payload_util import transfer_payload_type, check_topic, check_payload
from general_gateway.common.payload_format_util import read_request_can_do_task_content, read_task_payload, write_request_can_do_payload
from general_gateway.common.trace_error_util import trace_error, get_function_name
from general_gateway.models.enum.config_enum import ConfigEnum
from general_gateway.models.enum.message_enum import MessageType, MessageDirection, MessageStatus
from general_gateway.models.enum.project_name_enum import ProjectNameEnum
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.apps.fleet.models.enum.task_type import TaskType as FleetTaskType
from general_gateway.models.general.mqtt_message import MQTTMessage
from general_gateway.models.general.mqtt_task import MQTTTask
from general_gateway.models.mysql import MySQL
from general_gateway.services.task_manager import TaskManager
from general_gateway.common.datetime_utils import iso8601_format_to_string


colorama.init()

class Doorkeeper:
    _instance = None
    _initialized_ = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not Doorkeeper._initialized_:
            print("general_gateway doorkeeper")
            config = configparser.ConfigParser()
            config.read(ConfigEnum.FILE_NAME.value)

            self.host = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_BROKER_HOST.value]
            self.server_id = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_SERVER_ID.value]
            self.gateway_id = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_GATEWAY_ID.value]
            self.role = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_ROLE.value]
            self.project_name = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_PROJECT_NAME.value]

            self.mqtt_qos = 0
            self.mqtt_session_id = 1
            self.is_connecting_mqtt_broker = False

            # 20250516 楊皓宇
            redis_host = os.getenv('REDIS_HOST', 'iot_redis')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.r = redis.Redis(host=redis_host, port=redis_port)

            # 20240615 累積待發送訊息數量
            # self.msg_limit = 200

            # 20240701 random drop package test
            self.drop_rate = 0.1

            if self.role == "Server":
                self.subscribe_topic = self.server_id + "/from/#"
            elif self.role == "Gateway":
                self.subscribe_topic = self.server_id + "/to/" + self.gateway_id + "/#"
            else:
                raise Exception("role is Error")

            self.send_message_scheduler = BackgroundScheduler()
            # 20240402 定期檢查需要重新派送的訊息(未收到ack)
            self.resend_message_scheduler = BackgroundScheduler()
            # 20240324 定期刪除已發送訊息
            self.delete_timeout_message_scheduler = BackgroundScheduler()
            # 20240702 定期紀錄模組訊息收發throughput
            # self.record_throughput_scheduler = BackgroundScheduler()


            # 發訊息的排程，每秒發送1次
            self.send_message_interval_sec = 1
            # 定期清理無效訊息
            self.delete_timeout_message_sec = 3
            # 重傳訊息排程 (5秒)
            self.resend_message_interval_sec = 5
            # 20240403 ACK機制：連續重傳5次後，等待 5 分鐘在重新嘗試傳送
            self.message_timeout_sec = 300
            self.is_send_message_scheduler_starting = False
            
            # 20240715 for throughput test
            # self.queue_size = 50
            # self.messages_dict = {}
            # self.init_message_queue()
            # 20240715 end of adjust, only for test

            # 20240723 優化接收訊息的機制，接收訊息後會被放進queue，從queue裡面取出訊息處理(使用thread平行處理)
            self.receive_queue = queue.Queue()
            self.pool = ThreadPoolExecutor(max_workers=10)
            # 20240723 end of adjust

            self.resend_message_queue = {}
            self.r.set('send_message', '0'.encode('utf-8'))
            self.r.set('resend_message', '0'.encode('utf-8'))
            self._initialized_ = True
            # self.r.delete('ack_messages')
    
    def send_msg_listener(self, event):
        print("listener:", len(self.send_message_scheduler.get_jobs()))
        for job in self.send_message_scheduler.get_jobs():
            print("listener:", job.name, ",", job.id, ",", job.next_run_time)
        # if not event.exception:
        #     job = scheduler.get_job(event.job_id)
        #     if job.name == 'tick':
        #         scheduler.add_job(tack)

    # def resend_msg_listener(self, event):
    #     print("listener:", len(self.resend_message_scheduler.get_jobs()))
    #     for job in self.resend_message_scheduler.get_jobs():
    #         print("listener:", job.name, ",", job.id, ",", job.next_run_time)


    def start(self):
        print("doorkeeper: start")
        self._init_mqtt_client()
        self.send_message_scheduler.add_listener(self.send_msg_listener, EVENT_JOB_EXECUTED)
        # self.resend_message_scheduler.add_listener(self.resend_msg_listener, EVENT_JOB_EXECUTED)
        threading.Thread(target=self.message_handler, daemon=True).start()
        self.send_message_scheduler.add_job(
            self._send_message,
            'interval',
            seconds=self.send_message_interval_sec,
            id='_send_message',
            # coalesce=False,
            coalesce=True,
            max_instances=1
        )
        
        # 20240403 重新發送訊息(未收到ACK)
        self.resend_message_scheduler.add_job(
            self._resend_message,
            'interval',
            seconds=self.resend_message_interval_sec,
            id='_message_timeout',
            misfire_grace_time=self.resend_message_interval_sec,
            # coalesce=False,
            coalesce=True, 
            max_instances=1
        )

        self.delete_timeout_message_scheduler.add_job(
            self.delete_timeout_message,
            'interval',
            seconds=self.delete_timeout_message_sec,
            id='delete_timeout_message'
        )

        # self.set_send_message_scheduler()

    # 20240714 init message queue, only for throughput test
    def init_message_queue(self):
        if not self.messages_dict:
            for i in range(self.queue_size):
                message_id = str(uuid.uuid4())  # 使用唯一的ID
                coordinate_x = round(random.uniform(0.00, 100.00), 2)
                coordinate_y = round(random.uniform(0.00, 100.00), 2)
                timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]  # 使用更精確的時間格式
                content = {
                    "coordinate_x": coordinate_x,
                    "coordinate_y": coordinate_y,
                    "update_time": timestamp
                }

                payload = {
                    'header': {
                        'message_id': message_id,
                        'message_type': MessageType.REQUEST.value,  # 確保使用枚舉值
                        'message_timestamp': datetime.now().isoformat(),
                        'is_need_ack': True,
                        'task_sn': i + 1,
                        'task_id': i + 1,
                        'task_type': TaskType.SEND_POSITION.value,  # 確保使用枚舉值
                        'task_timeout': 1800,
                        'task_priority': 1,
                        'task_status': TaskStatus.SUCCEEDED.value,  # 確保使用枚舉值
                        'task_created_time': datetime.now().isoformat()
                    },
                    'content': content
                }

                mqtt_message = MQTTMessage(
                    message_sn=i + 1,
                    message_id=message_id,
                    is_publish=True,
                    session_sn=1,
                    gateway_sn=0,
                    task_sn=i + 1,
                    topic=f"{self.server_id}/from/{self.gateway_id}", 
                    payload=json.dumps(payload),
                    message_type=MessageType.REQUEST,
                    message_status=MessageStatus.UNSENT,
                    qos=0,
                    is_retain=False,
                    is_need_ack=True,
                    timestamp=datetime.now()
                )
                self.messages_dict[mqtt_message.message_sn] = mqtt_message

        # 20240715: end of adjust


    def _init_mqtt_client(self):
        self.client = mqtt.Client()
        self.client.on_connect = self._mqtt_on_connect
        self.client.on_disconnect = self._mqtt_on_disconnect
        self.client.on_message = self._mqtt_on_message
        self.client.on_subscribe = self._mqtt_on_subscribe
        # 20240622 reconnect mqtt broker within 5 seconds
        self.client.reconnect_delay_set(max_delay=5)

        try:
            # 與 MQTT Broker 異步連接(non-block function)
            self.client.connect_async(
                self.host, port=1883, keepalive=60, bind_address="")
            # loop_start()會啟動一個新的執行緒在背景中持續處理與 Broker 的連接狀態
            self.client.loop_start()
            print("Connect MQTT Broker Successfully!!!")
        except BaseException as e:
            print("---Connect Error---")
            print("Broker is Not online. Connect Later.")
            trace_error(e)

    def check_mqtt_rc(self, rc):
        self.rc = rc

        # 0：連接成功
        # 1：連接被拒絕 - 不正確的協議版本
        # 2：連接被拒絕 - 無效的客戶端標識符
        # 3：連接被拒絕 - 服務器不可用
        # 4：連接被拒絕 - 錯誤的用戶名或密碼
        # 5：連接被拒絕 - 未授權
        # 6-255：目前未使用

        if self.rc == 0:
            print("---Connected with MQTT Broker---")
            # 如果我們連線 或 重新連線時，程式將會重新訂閱主題
            self.is_connecting_mqtt_broker = True
            self.client.subscribe(self.subscribe_topic, qos=self.mqtt_qos)
        else:
            logging.warning("Disconnected with return code: %d\n")
            self.is_connecting_mqtt_broker = False
            print("---Disconnection---")

        print("Returned code:", self.rc)
        self.set_send_message_scheduler()
        

    def check_mqtt_flags(self, flags):
        if flags.get('session present') == 0:
            print("Session is alive, present: ",
                  str(flags.get('session present')))
        else:
            print("Session is clean, present: ",
                  str(flags.get('session present')))
    
    def _mqtt_on_connect(self, client, userdata, flags, rc):
        print()
        print("---on_connect---")
        self.check_mqtt_rc(rc)
        self.check_mqtt_flags(flags)


    def _mqtt_on_disconnect(self, client, userdata, rc):
        print("---_mqtt_on_disconnect---")
        self.check_mqtt_rc(rc)
    

    def _mqtt_on_message(self, client, userdata, msg):
        if self.role == "Server":
            server_id, direct, gateway_id = msg.topic.split('/')
            topic = f"{server_id}/to/{gateway_id}"
            self.client.publish(topic, msg.payload, qos=self.mqtt_qos)
        
        # 封包遺失模擬
        # if random.random() <= self.drop_rate:
        #     return
        
        print("---_mqtt_on_message---")
        print("Topic:", msg.topic)
        self.receive_queue.put((msg.topic, msg.payload.decode("utf-8")))

    def _mqtt_on_subscribe(self, client, userdata, mid, granted_qos):
        print("---_mqtt_on_subscribe---")
        print(self.role, "Subscribe:", self.subscribe_topic)

    def set_send_message_scheduler(self):
        try:
            if self.is_send_message_scheduler_starting:
                self.send_message_scheduler.resume()
                # self.resend_message_scheduler.resume()
                self.delete_timeout_message_scheduler.resume()

                # 20240702 
                # self.record_throughput_scheduler.resume()
            else:
                self.send_message_scheduler.start()
                # self.resend_message_scheduler.start()
                self.delete_timeout_message_scheduler.start()
                self.is_send_message_scheduler_starting = True

            # else:
            #     self.send_message_scheduler.pause()
            #     self.resend_message_scheduler.pause()
            #     self.delete_timeout_message_scheduler.pause()

        except BaseException as e:
            trace_error(e)

    def message_handler(self):
        while True:
            topic, payload_str = self.receive_queue.get()
            payload = transfer_payload_type(payload_str, to_type=dict)
            self.pool.submit(self.deal_message, topic, payload)
            self.receive_queue.task_done()

    # 20240717 end of adjust
    def deal_message(self, topic, payload):
        try:
            # 1.檢查 MQTT topic 格式
            if not check_topic(topic):
                raise Exception("Topic format error")

            # 2.檢查 payload 格式
            if not check_payload(payload):
                raise Exception("Payload format error")
            
            mqtt_message = MQTTMessage(
                is_publish=False,
                message_id=payload.get('header').get('message_id'),
                task_sn=payload.get('header').get('task_sn'),
                topic=topic,
                payload=payload,
                message_type=MessageType(
                    payload.get('header').get('message_type')),
                message_status=payload.get('header').get('message_status'),
                is_need_ack=payload.get('header').get('is_need_ack'),
                timestamp=datetime.now().isoformat()
            )
            # print("Message id:", mqtt_message.message_id)
            if mqtt_message.message_type == MessageType.REQUEST or mqtt_message.message_type == MessageType.RESPONSE:
                print(mqtt_message.message_id, mqtt_message.timestamp)
                update_done_message_in_message_log_only_timestamp(mqtt_message=mqtt_message)
                return
            
                if mqtt_message.is_need_ack:
                    self.create_ack_message(mqtt_message)
                    # print("payload: ", payload)
                    # print("timestamp: ", mqtt_message.timestamp)

                mqtt_task = read_task_payload(
                    mqtt_message.topic,
                    mqtt_message.payload
                )

                if mqtt_message.message_type == MessageType.REQUEST:
                    insert_mqtt_task(mqtt_task)
                    # 將任務派發出去
                    TaskManager().add_task_sn_to_task_list(
                        mqtt_task.task_sn, mqtt_message.message_type
                    )
                    self.r.set('has_tasks', '1'.encode('utf-8'))
                else:
                    update_mqtt_task_by_task_sn_and_gateway_sn(mqtt_task)

                    TaskManager().add_task_sn_to_task_list(
                        mqtt_task.task_sn, mqtt_message.message_type
                    )
                    # 將任務派發出去
                    self.r.set('has_tasks', '1'.encode('utf-8'))
            elif mqtt_message.message_type == MessageType.ACK:

                self.deal_ack_message(ack_message=mqtt_message)
                # remove message in queue
                if mqtt_message.message_id in self.resend_message_queue.keys():
                    del self.resend_message_queue[mqtt_message.message_id]

                # 20240614 deal_ack_message
                mqtt_message.message_status = MessageStatus.DONE
                mqtt_message.is_publish = 1
                mqtt_message.is_need_ack = 0
                mqtt_message.task_sn = 0
                # 20240701 update mqtt_message_log
                update_done_message_in_message_log_no_timestamp(mqtt_message=mqtt_message)
                # update_done_message_in_message_log(mqtt_message=mqtt_message)
            else:
                raise Exception("Unknown message type")
        except BaseException as e:
            trace_error(e)
            return False

    # def deal_request_can_do_message(self, mqtt_message: MQTTMessage):
    #     # TODO: Doorkeeper可處理簡單的訊息，分流訊息後再執行，function name可以有doorkeeper字眼
    #     gateway_id, gateway_sn = self.get_mqtt_gateway_id_and_sn_in_mqtt_message(
    #         mqtt_message)
    #     request_can_do_task_list, can_do_task_list, can_not_do_task_list = \
    #         read_request_can_do_task_content(mqtt_message)

    #     if request_can_do_task_list:
    #         mqtt_tasks = self._check_request_can_do_task(
    #             request_can_do_task_list, gateway_sn)
    #         self._return_can_do_and_can_not_do_task_list(
    #             request_can_do_task_list,
    #             mqtt_tasks,
    #             mqtt_message
    #         )
    #     else:
    #         if can_not_do_task_list:
    #             self._deal_can_not_do_task(can_not_do_task_list, gateway_sn)
    #         else:
    #             self._deal_can_do_task(can_do_task_list, gateway_sn)

    # def _check_request_can_do_task(self, request_can_do_task_list: list, gateway_sn):
    #     mqtt_tasks = select_mqtt_tasks(
    #         task_sn_list=request_can_do_task_list, gateway_sn=gateway_sn)

    #     if mqtt_tasks:
    #         return mqtt_tasks
    #     else:
    #         return False

    # def _return_can_do_and_can_not_do_task_list(self, request_can_do_task_list: list, mqtt_tasks, mqtt_message):
    #     can_do_task_list = []

    #     if mqtt_tasks:
    #         for mqtt_task in mqtt_tasks:
    #             can_do_task_list.append(mqtt_task.task_sn)

    #         can_not_do_task_list = list(
    #             set(request_can_do_task_list) - set(can_do_task_list)
    #         )
    #     else:
    #         can_not_do_task_list = request_can_do_task_list

    #     payload = write_request_can_do_payload(
    #         is_need_ack=True,
    #         message_type=MessageType.RESPONSE,
    #         can_do_mqtt_tasks=can_do_task_list,
    #         can_not_do_mqtt_tasks=can_not_do_task_list)

    #     add_to_mqtt_message(
    #         is_need_ack=True,
    #         message_type=MessageType.RESPONSE,
    #         direction=MessageDirection.TO,
    #         payload=payload,
    #         gateway_id=self.gateway_id
    #     )

    # def _deal_can_do_task(self, can_do_task_list: list, gateway_sn):
    #     mqtt_task = MQTTTask(task_sn=can_do_task_list,
    #                          gateway_sn=gateway_sn, task_status=TaskStatus.DOING)
    #     result = update_mqtt_task_status_by_mqtt_task(
    #         mqtt_task=mqtt_task
    #     )

    #     return result

    # def _deal_can_not_do_task(self, can_not_do_task_list: list, gateway_sn):
    #     result = delete_mqtt_task_from_can_not_do_task_list(
    #         can_not_do_task_list, gateway_sn)
    #     return result


    # 20240716 for Throughput Test
    # def _send_message(self):
    #     send_message = self.r.get('send_message').decode('utf-8')
    #     if send_message == '1':
    #         return

    #     self.r.set('send_message', '1'.encode('utf-8'))
    #     try:
    #         for message_sn, message in self.messages_dict.items():
    #             new_message_id = str(uuid.uuid4())
    #             payload_dict = json.loads(message.payload)
    #             payload_dict['header']['message_timestamp'] = datetime.now().isoformat()
    #             payload_dict['header']['message_id'] = new_message_id

    #             mqtt_message = MQTTMessage(
    #                 message_id=new_message_id,
    #                 topic=message.topic,
    #                 is_publish=True,
    #                 task_sn=message.task_sn,
    #                 session_sn=1,
    #                 gateway_sn=0,
    #                 message_type=MessageType.REQUEST,
    #                 message_status=MessageStatus.WAITING_FOR_ACK,
    #                 qos=0,
    #                 is_retain=False,
    #                 is_need_ack=True,
    #                 timestamp=datetime.now().astimezone()
    #             )

    #             mqtt_message.payload = json.dumps(payload_dict)

    #             self.client.publish(mqtt_message.topic, mqtt_message.payload, qos=self.mqtt_qos)
    #             insert_app_message_log(mqtt_message)

    #     except BaseException as e:
    #         trace_error(e)
    #         return False
    #     finally:
    #         self.r.set('send_message', '0'.encode('utf-8'))

    # 發送訊息的人，排程執行 (不斷撈取訊息)
    def _send_message(self):
        send_message = self.r.get('send_message').decode('utf-8')
        print()
        # 判斷是否有在執行發送訊息
        if send_message == '1':
            return

        self.r.set('send_message', '1'.encode('utf-8'))
        try:
            # resend
            # messages = self.fetch_need_republish_messages()
            # print("fetch time: ", datetime.now().isoformat())
            # print("msg count: ", len(messages))
            
            # if messages is not None:
            #     for message in messages:
            #         mqtt_message = MQTTMessage(
            #             message_id = message.get('message_id'),
            #             topic = message.get('topic'),
            #             payload = message.get('payload'),
            #             message_type = MessageType(message.get('message_type'))
            #         )

            #         if mqtt_message.message_id in self.resend_message_queue.keys() and self.resend_message_queue.get(mqtt_message.message_id, {}).get('last_resend_time') + timedelta(seconds=5) < datetime.now():
            #             payload_dict = json.loads(mqtt_message.payload)
            #             payload_dict['header']['message_timestamp'] = datetime.now().isoformat()
            #             mqtt_message.payload = json.dumps(payload_dict)

            #             self.client.publish(mqtt_message.topic, mqtt_message.payload, qos=self.mqtt_qos)
                       
            #             resend_times = self.resend_message_queue.get(mqtt_message.message_id).get('resend_times') + 1
            #             self.resend_message_queue[mqtt_message.message_id] = {
            #                 'last_resend_time': datetime.now(),
            #                 'resend_times': resend_times
            #             }
                        
            #             # 20240701 record resend times
            #             update_message_log(resend_times, mqtt_message=mqtt_message)

            #         elif self.resend_message_queue.get(mqtt_message.message_id, {}).get('resend_times', 0) >= 10:
            #             self.resend_message_queue[mqtt_message.message_id] = {
            #                 'last_resend_time': datetime.now()+timedelta(minutes=15),
            #                 'resend_times': 0
            #             }

            # send
            messages = self.fetch_need_publish_messages()
            # print("fetch time: ", datetime.now().isoformat())
            # print("msg count: ", len(messages))
            
            if messages is not None:
                for message in messages:
                    mqtt_message = MQTTMessage(
                        message_id = message.get('message_id'),
                        topic = message.get('topic'),
                        payload = message.get('payload'),
                        message_type = MessageType(message.get('message_type'))
                    )

                    # 20240504 record publish time
                    payload_dict = json.loads(mqtt_message.payload)
                    payload_dict['header']['message_timestamp'] = datetime.now().isoformat()
                    mqtt_message.payload = json.dumps(payload_dict)
                    # end of adjust

                    self.client.publish(mqtt_message.topic, mqtt_message.payload, qos=self.mqtt_qos)

                    print("_send_message: published")
                    if bool(message.get('is_need_ack')) is True:
                        status=MessageStatus.WAITING_FOR_ACK    
                        update_mqtt_message_status_by_message_id(
                            mqtt_message.message_id,
                            status
                        )
                        self.resend_message_queue[mqtt_message.message_id] = {
                            'last_resend_time': datetime.now(),
                            'resend_times': 0
                        }
                        mqtt_message.message_status = status
                        update_message_log(mqtt_message=mqtt_message)
                    else:
                        status=MessageStatus.DONE
                        update_mqtt_message_status_by_message_id(
                            mqtt_message.message_id,
                            status
                        )

                        mqtt_message.message_status = status
                        # 20250602 payload改回來
                        update_message_log_without_payload_timestamp(mqtt_message=mqtt_message)
                        delete_DONE_mqtt_message()

        except BaseException as e:
            trace_error(e)
            return False
        finally:
            # 將派發訊息設為 0
            self.r.set('send_message', '0'.encode('utf-8'))

    # # 訊息重傳
    def _resend_message(self):
        resend_message = self.r.get('resend_message').decode('utf-8')
        print()
        # 判斷是否有在執行重發訊息
        if resend_message == '1':
            return

        self.r.set('resend_message', '1'.encode('utf-8'))
        try:
            # _resend_msg_start = time.process_time()
            messages = self.fetch_need_republish_messages()
            if messages is not None:
                for message in messages:
                    mqtt_message = MQTTMessage(
                        message_id = message.get('message_id'),
                        topic = message.get('topic'),
                        payload = message.get('payload'),
                        message_type = MessageType(message.get('message_type'))
                    )

                    # if self.resend_message_queue.get(message_id, {}).get('last_resend_time') + timedelta(minutes=5) > datetime.now() and self.resend_message_queue.get(message_id, {}).get('resend_times', 0) < 10:
                    if mqtt_message.message_id in self.resend_message_queue.keys() and self.resend_message_queue.get(mqtt_message.message_id, {}).get('last_resend_time') + timedelta(seconds=5) < datetime.now():
                        payload_dict = json.loads(mqtt_message.payload)
                        payload_dict['header']['message_timestamp'] = datetime.now().isoformat()
                        mqtt_message.payload = json.dumps(payload_dict)

                        self.client.publish(mqtt_message.topic, mqtt_message.payload, qos=self.mqtt_qos)
                       
                        resend_times = self.resend_message_queue.get(mqtt_message.message_id).get('resend_times') + 1
                        self.resend_message_queue[mqtt_message.message_id] = {
                            'last_resend_time': datetime.now(),
                            'resend_times': resend_times
                        }
                        
                        # 20240701 record resend times
                        update_message_log(resend_times, mqtt_message=mqtt_message)

                    elif self.resend_message_queue.get(mqtt_message.message_id, {}).get('resend_times', 0) >= 10:
                        self.resend_message_queue[mqtt_message.message_id] = {
                            'last_resend_time': datetime.now()+timedelta(minutes=15),
                            'resend_times': 0
                        }

                    # else:
                    #     print(f"Resend_message {mqtt_message.message_id}: could not published")
                    #     update_mqtt_message_status_by_message_id(mqtt_message.message_id, status=MessageStatus.FAILED)
                    #     delete_FAILED_mqtt_message()
                    #     del self.resend_message_queue[mqtt_message.message_id]

        except BaseException as e:
            trace_error(e)
            return False
        finally:
            # 將派發訊息設為 0
            self.r.set('resend_message', '0'.encode('utf-8'))


    def delete_timeout_message(self):
        print()
        try:
            delete_FAILED_mqtt_message()
            delete_DONE_mqtt_message()

        except BaseException as e:
            trace_error(e)
            return False
    
    def create_ack_message(self, mqtt_message: MQTTMessage):
        """
        :param mqtt_message:
        :return: Boolean
        """

        try:
            print("-" * 10)
            print("(回傳)送達通知:\n")

            gateway_id, gateway_sn = self.get_mqtt_gateway_id_and_sn_in_mqtt_message(
                mqtt_message)
            direct = self.get_direct_in_mqtt_message(mqtt_message)
            if MessageDirection(direct) == MessageDirection.TO:
                direct = MessageDirection.FROM
            elif MessageDirection(direct) == MessageDirection.FROM:
                direct = MessageDirection.TO
            else:
                raise Exception("Invalid direct")

            ack_payload = "{}"

            result = add_to_mqtt_message(
                message_id=mqtt_message.message_id,
                message_type=MessageType.ACK,
                payload=ack_payload,
                gateway_sn=gateway_sn,
                task_sn=mqtt_message.task_sn,
                is_need_ack=False,
                direction=direct,
                gateway_id=gateway_id
            )

            mqtt_message.payload = transfer_payload_type(mqtt_message.payload, to_type=str)
            update_payload_and_timestamp_in_message_log(mqtt_message=mqtt_message)

            return result
        
        except BaseException as e:
            trace_error(e)
            return False
    
    def deal_ack_message(self, ack_message: MQTTMessage):
        """
        :param ack_message:
        :return: Boolean
        """
        try:
            # deal_ack_msg_start = time.process_time()
            # current_time = datetime.now()
            # print("Ack receive time: ", current_time.strftime("%H:%M:%S.%f"))
            print("-" * 10)
            print("(接收)送達通知:\n")

            # published_message = select_mqtt_message_by_message_id(
            #     ack_message.message_id)
            published_message = select_message_from_message_log(
                ack_message.message_id
            )

            published_message_payload = transfer_payload_type(
                published_message.payload, to_type=dict
            )

            task_type = None
            if published_message_payload.get('header').get('task_type') is not None:
                task_type = FleetTaskType(
                        published_message_payload.get('header').get('task_type'))
            task_sn = published_message_payload.get('header').get('task_sn')

            # print("deal_ack_message: published_message.message_type:", published_message.message_type)

            server_id, direct, gateway_id = ack_message.topic.split(
                '/')
            mqtt_gateway = select_mqtt_gateways(gateway_id)

            if MessageType(published_message.message_type) is MessageType.REQUEST:
                mqtt_task = MQTTTask(
                    task_sn=task_sn,
                    gateway_sn=mqtt_gateway[0].gateway_sn,
                    task_status=TaskStatus.DISPATCHED,
                    task_type=task_type
                )
                update_mqtt_task_status_by_mqtt_task(
                    mqtt_task=mqtt_task
                )

            elif MessageType(published_message.message_type) is MessageType.RESPONSE:
                mqtt_task = MQTTTask(
                    task_sn=task_sn,
                    gateway_sn=mqtt_gateway[0].gateway_sn,
                    task_status=TaskStatus.TERMINATED,
                    task_type=task_type
                )
                update_mqtt_task_status_by_mqtt_task(
                    mqtt_task=mqtt_task
                )
                delete_mqtt_task_where_terminated()
            else:
                return False
            
            update_mqtt_message_status_by_message_id(
                message_id=ack_message.message_id,
                status=MessageStatus.DONE
            )
            
            return True
        except Exception as e:
            trace_error(e)
            return False

    def fetch_need_publish_messages(self, **principle):
        results = None
        try:
            # fetch_publish_msg_start = time.process_time()
            # 如果有原則，依照原則，組成 sql 語法撈取 message
            if principle:
                sql = "SELECT * FROM `mqtt_message` WHERE "
                print("-" * 10)
                sql_order = None
                sql_end = None
                for key in principle.keys():
                    if key == "limit":
                        key_value = principle[key]
                        sql_end = " limit {}".format(key_value)
                    elif key == "asc":
                        key_value = principle[key]
                        sql_order = " order by `{}` ASC".format(key_value)
                    elif key == "desc":
                        key_value = principle[key]
                        sql_order = " order by `{}` DESC".format(key_value)
                    else:
                        key_value = principle[key]
                        sql += " `{}` = '{}'".format(key, key_value)

                if sql_order:
                    sql += sql_order
                if sql_end:
                    sql += sql_end

            # 如果沒有原則，依照預設方式撈取 message ( timestamp 順序)
            # 20240403 只發送"未發送"的訊息
            else:
                sql = (
                    "SELECT * FROM `mqtt_message` "
                    "WHERE `message_status` IN ('{}') "
                    "AND `schedule_time` <= NOW() "
                    "ORDER BY `priority` ASC "
                ).format(MessageStatus.UNSENT.value)

            db = MySQL()
            cprint("Doorkeeper:" + get_function_name(), "yellow")
            results = db.query(sql)
            # print("fetch_need_publish_messages: result:", results)
            db.close()
        except Exception as e:
            trace_error(e)
        finally:
            if results:
                pass
                # print("-" * 10)
                # print("Fetch:")
                # print(results)
                # print("-" * 10)
            # fetch_publish_msg_end = time.process_time()
            # print("fetch publish time: %f" % (fetch_publish_msg_end - fetch_publish_msg_start))
            return results

    def fetch_need_republish_messages(self, **principle):
        results = None
        try:
            # fetch_republish_msg_start = time.process_time()
            # 如果有原則，依照原則，組成 sql 語法撈取 message
            if principle:
                print("---principle republish---!!!")
                sql = "SELECT * FROM `mqtt_message` WHERE "
                print("-" * 10)
                sql_order = None
                sql_end = None
                for key in principle.keys():
                    if key == "limit":
                        key_value = principle[key]
                        sql_end = " limit {}".format(key_value)
                    elif key == "asc":
                        key_value = principle[key]
                        sql_order = " order by `{}` ASC".format(key_value)
                    elif key == "desc":
                        key_value = principle[key]
                        sql_order = " order by `{}` DESC".format(key_value)
                    else:
                        key_value = principle[key]
                        sql += " `{}` = '{}'".format(key, key_value)

                if sql_order:
                    sql += sql_order
                if sql_end:
                    sql += sql_end

            # 如果沒有原則，依照預設方式撈取 message ( timestamp 順序)
            else:
                print("---Republish by order---\n\n")
                sql = (
                    "SELECT * FROM `mqtt_message` "
                    "WHERE `message_status` IN ('{}') "
                    "AND `schedule_time` <= NOW() "
                    "ORDER BY `priority` ASC "
                ).format(MessageStatus.WAITING_FOR_ACK.value)

            db = MySQL()
            cprint("Doorkeeper:" + get_function_name(), "yellow")
            results = db.query(sql)
            # print("Republish_messages: result:", results)
            db.close()

            # fetch_republish_msg_end = time.process_time()
            # fetch_republish_msg = fetch_republish_msg_end - fetch_republish_msg_start
            # print("fetch republish msg time: %f" % (fetch_republish_msg))
        except Exception as e:
            trace_error(e)
        finally:
            if results:
                # print("-" * 10)
                # print("Fetch:")
                # print(results)
                # print("-" * 10)
                pass
            return results

    def get_mqtt_gateway_id_and_sn_in_mqtt_message(self, mqtt_message):
        server_id, direct, gateway_id = mqtt_message.topic.split("/")
        mqtt_gateway = select_mqtt_gateways(gateway_id)
        gateway_sn = mqtt_gateway[0].gateway_sn
        return gateway_id, gateway_sn

    def get_direct_in_mqtt_message(self, mqtt_message):
        server_id, direct, gateway_id = mqtt_message.topic.split("/")
        return direct