# app functions：
    # app_get_position：向閘道器索取代步車定位資訊
    # app_get_position_result：伺服器回傳定位資訊結果
    # app_send_position：閘道器向伺服器傳送定位資訊
    # app_get_navigation_record：向閘道器索取代步車歷史路徑
    # app_send_navigation_record：向伺服器傳送代步車歷史路徑

import configparser
import threading
import math, time
from datetime import datetime

import json
from flask import jsonify
from general_gateway.apps.fleet.db_fleet import select_latest_coordinate, insert_vehicle_coordinate
from general_gateway.apps.fleet.models.enum.task_type import TaskType
from general_gateway.common.datetime_utils import datetime_format
from general_gateway.common.db_utils import update_mqtt_task_status_by_mqtt_task, add_to_mqtt_message, \
    delete_mqtt_task_where_terminated, select_mqtt_tasks, insert_mqtt_device, insert_mqtt_task, \
    list_to_tuple_string
from general_gateway.common.mqtt_payload_util import transfer_payload_type
from general_gateway.common.trace_error_util import trace_error, get_function_name
from general_gateway.models.enum.config_enum import ConfigEnum
from general_gateway.models.enum.datetime_enum import DateTimeType
from general_gateway.models.enum.message_enum import MessageType, MessageDirection
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.models.general.mqtt_task import MQTTTask
from general_gateway.models.mysql import MySQL
from setting import DB_CONFIG, BROKER_HOST, SERVER_ID, GATEWAY_ID, ROLE, GATEWAY_SN

from general_gateway.apps.fleet.models.app_cmd import CMD
from general_gateway.common.datetime_utils import string_convert_to_date, date_plus_hours, \
    ymdHMS_format_to_string, data_plus_seconds
from general_gateway.apps.fleet.models.enum.task_type import CMDStatus, CMDType, CMDLayer
from typing import Optional
from datetime import datetime, date, timedelta

class AppExecutor(threading.Thread):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        threading.Thread.__init__(self)

        config = configparser.ConfigParser()
        config.read(ConfigEnum.FILE_NAME.value)

        self.gateway_id = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_GATEWAY_ID.value]
        self.role = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_ROLE.value]
        # self.G_CONTROL_VALUE_TYPE_LIST = [int(config[ConfigEnum.CUSTOM.value]['G_CONTROL_VALUE_TYPE_LIST'])]
        # initialize app_pick_up_cmd()：定期撈取指令
        # self.app_pick_up_cmd()

    def app_dispatch(self, mqtt_task: MQTTTask, message_type: MessageType):
        print("\n Dispatcher!!! \n")
        try:
            if mqtt_task.task_type is TaskType.SEND_POSITION and message_type is MessageType.REQUEST:
                self.app_send_position(mqtt_task)
            elif mqtt_task.task_type is TaskType.GET_POSITION and message_type is MessageType.REQUEST:
                self.app_get_position(mqtt_task)
            elif mqtt_task.task_type is TaskType.GET_POSITION and message_type is MessageType.RESPONSE:
                self.app_get_position_result(mqtt_task)

        except BaseException as e:
            trace_error(e)
            return False

    def app_tasks_finished(self, task_type):
        try:
            print()
            print("---回傳任務結果---")
            done_tasks = select_mqtt_tasks(
                task_type=task_type,
                task_status=TaskStatus.SUCCEEDED
            )
            failed_tasks = select_mqtt_tasks(
                task_type=task_type,
                task_status=TaskStatus.FAILED
            )

            if self.role == "Gateway":
                direct = MessageDirection.FROM
            else:
                direct = MessageDirection.TO

            if done_tasks:
                for mqtt_task in done_tasks:
                    if task_type == TaskType.SEND_POSITION \
                            or task_type == TaskType.GET_POSITION:
                        mqtt_task.content = {}

                    add_to_mqtt_message(
                        is_need_ack=True,
                        message_type=MessageType.RESPONSE,
                        mqtt_task=mqtt_task,
                        direction=MessageDirection.FROM,
                        gateway_id=self.gateway_id
                    )

            if failed_tasks:
                for mqtt_task in failed_tasks:
                    add_to_mqtt_message(
                        is_need_ack=True,
                        message_type=MessageType.RESPONSE,
                        mqtt_task=mqtt_task,
                        direction=MessageDirection.FROM,
                        gateway_id=self.gateway_id
                    )
        except BaseException as e:
            trace_error(e)
            return False
    
    def app_return_message(self, mqtt_task: MQTTTask):
        try:
            print("-" * 10)
            print(mqtt_task.content)
            print("-" * 10)

            if self.role == "Gateway":
                direct = MessageDirection.FROM
            else:
                direct = MessageDirection.TO

            result = add_to_mqtt_message(
                is_need_ack=True,
                message_type=MessageType.RESPONSE,
                mqtt_task=mqtt_task,
                direction=direct,
                gateway_id=self.gateway_id
            )

            if not result:
                raise Exception("Insert mqtt_message Fail.")
        except BaseException as e:
            trace_error(e)
            return False
        
    def app_get_position(self, mqtt_task: MQTTTask):
        result = None
        coordinate_x = None
        coordinate_y = None
        update_time = None

        try:
            app_get_position_start = time.process_time()
            print()
            print("---獲取代步車即時座標---")
             
            mqtt_task.task_status = TaskStatus.DOING
            update_mqtt_task_status_by_mqtt_task(
                mqtt_task=mqtt_task
            )
            query_results = select_latest_coordinate()
            if not query_results:
                result = False
                raise Exception("Query newest position Fail.")

            for position in query_results:
                coordinate_x = position.get('coordinate_x')
                coordinate_y = position.get('coordinate_y')
                update_time = datetime_format(
                                position.get('update_time'),
                                from_datetime_type=DateTimeType.YMDHMS_FORMAT,
                                to_datetime_type=DateTimeType.ISO8601_FORMAT
                            )
            result = True
        except BaseException as e:
            trace_error(e)
        finally:
            if result:
                mqtt_task.task_status = TaskStatus.SUCCEEDED
                mqtt_task.content = {
                    "coordinate_x": coordinate_x,
                    "coordinate_y": coordinate_y,
                    "update_time": update_time
                }
            else:
                mqtt_task.task_status = TaskStatus.FAILED

            update_mqtt_task_status_by_mqtt_task(
                mqtt_task=mqtt_task
            )

            self.app_return_message(mqtt_task)
            app_get_position_end = time.process_time()
            print("app get position time: %f" % (app_get_position_end - app_get_position_start))
            return result
        
    def app_get_position_result(self, mqtt_task: MQTTTask):
        result = None
        try:
            app_get_position_result_start = time.process_time()
            print()
            print("---獲取代步車即時座標_同步回傳---")
            mqtt_task.task_status = TaskStatus.DOING
            update_mqtt_task_status_by_mqtt_task(
                mqtt_task=mqtt_task
            )
            if self.role == "Server" and mqtt_task.content is not None:
                content = transfer_payload_type(mqtt_task.content, to_type=dict)

                coordinate_x = content.get('coordinate_x')
                coordinate_y = content.get('coordinate_y')
                update_time = content.get('update_time')
                if mqtt_task.task_status is TaskStatus.FAILED:
                    print("Get Vehicle Coordinate Failed!!!")
                else:
                    insert_vehicle_coordinate(coordinate_x, coordinate_y, update_time)
                    mqtt_task.task_status = TaskStatus.TERMINATED
                    update_mqtt_task_status_by_mqtt_task(
                        mqtt_task=mqtt_task
                    )
                result = delete_mqtt_task_where_terminated()
            
                app_get_position_result_end = time.process_time()
                print("app get position result time: %f" % (app_get_position_result_end - app_get_position_result_start))
                
                return result
        except BaseException as e:
            trace_error(e)
            return False

    # Gateway to Server：傳送座標
    def app_send_position(self, mqtt_task: MQTTTask):
        result = None
        coordinate_x = None
        coordinate_y = None
        update_time = None
        try:
            print()
            print("\n\n------定期發送代步車座標------\n\n")
            app_send_position_start = time.process_time()
            mqtt_task.task_status = TaskStatus.DOING
            update_mqtt_task_status_by_mqtt_task(
                mqtt_task=mqtt_task
            )
            if self.role == "Server" and mqtt_task.content is not None:
                content = transfer_payload_type(mqtt_task.content, to_type=dict)

                coordinate_x = content.get('coordinate_x')
                coordinate_y = content.get('coordinate_y')
                update_time = content.get('update_time')
                if mqtt_task.task_status is TaskStatus.FAILED:
                    print("Get Vehicle Coordinate Failed!!!")
                else:
                    insert_vehicle_coordinate(coordinate_x, coordinate_y, update_time)
                    mqtt_task.task_status = TaskStatus.TERMINATED
                    update_mqtt_task_status_by_mqtt_task(
                        mqtt_task=mqtt_task
                    )
                result = delete_mqtt_task_where_terminated()
                app_send_position_end = time.process_time()
                print("App Send Position time: %f" % (app_send_position_end - app_send_position_start))
                return result
        except BaseException as e:
            trace_error(e)
            return False

        
# 20240129 test mqtt msg passing speed comment out
#     # 指令分派者
#     def cmd_dispatch(self,cmd: CMD):
#         try:
#             if cmd.cmd_type is CMDType.BATTERY :
#                 self.app_send_battery(cmd)
#             elif cmd.cmd_type is CMDType.AVOIDANCE:
#                 self.app_send_avoidance(cmd)
#             elif cmd.cmd_type is CMDType.SPEED:
#                 self.app_send_speed(cmd)
#             elif cmd.cmd_type is CMDType.IS_FAULT:
#                 self.app_send_is_fault(cmd)
#             # elif cmd.cmd_type is CMDType.POSITION:
#             #     self.cmd_send_position

#         except BaseException as e:
#             trace_error(e)
#             return False

#     def cmd_send_position(self,cmd: CMD):

#         try:
#             if self.role == "Gateway":
#                 query_results = select_latest_coordinate()

#                 if not query_results:
#                     result = False
#                     raise Exception("Query newest position Fail.")

#                 for position in query_results:
#                     coordinate_x = position.get('coordinate_x')
#                     coordinate_y = position.get('coordinate_y')
#                     update_time = datetime_format(
#                                     position.get('update_time'),
#                                     from_datetime_type=DateTimeType.YMDHMS_FORMAT,
#                                     to_datetime_type=DateTimeType.ISO8601_FORMAT
#                                 )
#                 payload = json.dumps({
#                     "coordinate_x": coordinate_x,
#                     "coordinate_y": coordinate_y,
#                     "timestamp": update_time

#                 })
                
#                 cmd = CMD(
#                     cmd_type=CMDType.POSITION,
#                     cmd_status=CMDStatus.CREATED,
#                     cmd_priority = 3,
#                     source =CMDLayer.DATA_APPLICATION_LAYEE,
#                     destination = CMDLayer.VEHICLE_CONTROL_LAYER,
#                     content=payload
#                 )

#                 print("cmd:", cmd)
#                 cmd.cmd_sn = insert_cmd_info(cmd)

#                 if not cmd.cmd_sn:
#                     raise Exception("Insert cmd " +
#                                     str(cmd.cmd_sn) + " Fail.")
            
#             else:
#                 print("---Server Send Get Position REQUEST !!!---")


#         except BaseException as e:
#             trace_error(e)
#             return False

#     def app_send_battery(self,cmd: CMD):
#         result = None
#         update_time = None

#         try:
#             print()
#             print("---獲取代步車電量---")
#             cmd.cmd_status = CMDStatus.DOING
#             update_cmd_status_by_cmd(cmd=cmd)

#         except BaseException as e:
#             trace_error(e)
#             return False
        
#     def app_send_avoidance(self,cmd: CMD):
#         result = None
#         update_time = None

#         try:
#             print()
#             print("---傳送代步車避障訊息---")
#             cmd.cmd_status = CMDStatus.DOING
#             update_cmd_status_by_cmd(cmd=cmd)
#             # result = delete_cmd_where_terminated()


#             # payload = json.dumps({
#             # })
            
#             # cmd_1 = CMD(
#             #     cmd_type=CMDType.STOP,
#             #     cmd_status=CMDStatus.CREATED,
#             #     cmd_priority = 1,
#             #     source =CMDLayer.DATA_APPLICATION_LAYEE,
#             #     destination = CMDLayer.VEHICLE_CONTROL_LAYER,
#             #     content=payload
#             # )

#             # print("cmd:", cmd_1)
#             # cmd_1.cmd_sn = insert_cmd_info(cmd_1)

#             # if not cmd_1.cmd_sn:
#             #     raise Exception("Insert cmd " +
#             #                     str(cmd_1.cmd_sn) + " Fail.")
#             result = True

#         except BaseException as e:
#             trace_error(e)
#             return False
#         finally:
#             # if result:
#             #     cmd_1.cmd_status = CMDStatus.SUCCEEDED
#             # else:
#             #     cmd_1.cmd_status = CMDStatus.FAILED

#             # update_cmd_status_by_cmd(cmd=cmd_1)

#             return result
    
#     def app_send_speed(self,cmd: CMD):
#         result = None
#         update_time = None

#         try:
#             print()
#             print("---傳送代步車速度訊息---")
#             cmd.cmd_status = CMDStatus.DOING
#             update_cmd_status_by_cmd(cmd=cmd)
#             # cmd.content = {'speed': 20}
#             # update_cmd_content(cmd = cmd)

#         except BaseException as e:
#             trace_error(e)
#             return False
        
#     def app_send_is_fault(self,cmd: CMD):
#         result = None
#         update_time = None

#         try:
#             print()
#             print("---傳送代步車故障碼訊息---")
#             cmd.cmd_status = CMDStatus.DOING
            
#             # app function operation

#             # update_cmd_status_by_cmd(cmd=cmd)
#             # delete_cmd_info(cmd=cmd)

#         except BaseException as e:
#             trace_error(e)
#             return False

#     #定期從ross_level_cmd_info資料表取出資料，並確認該指令時間是否過期，並分派指令
#     def app_pick_up_cmd(self):
#         print(" app_pick_up_cmd START !!!!!!!!")
#         sql = ("SELECT * FROM `app_cmd_info` "
#               "WHERE `destination` like '%data_application_layer%' AND `cmd_status` = 0 "
#               "ORDER BY `cmd_priority` ASC, `created_time` ASC limit 1")
        
#         ##從app_cmd_info資料表取出資料

#         db = MySQL()
#         cmds = db.query(sql)
#         print("cmds",cmds)

#         ##分別處理取出的指令資料
#         if cmds:
#             for cmd in cmds:
#                 cmd = CMD(
#                         cmd_sn=cmd.get('cmd_sn'),
#                         cmd_type= cmd.get('cmd_type'),
#                         cmd_status=CMDStatus(cmd.get('cmd_status')),
#                         cmd_timeout=cmd.get('cmd_timeout'),
#                         cmd_priority=cmd.get('cmd_priority'),
#                         content=json.loads(cmd.get('content')),
#                         created_time=string_convert_to_date(
#                             str(cmd.get('created_time')),
#                             datetime_type=DateTimeType.YMDHMS_FORMAT
#                         ),
#                     )
                

#                 task_timeout = data_plus_seconds(
#                     cmd.created_time, cmd.cmd_timeout)
#                 now = datetime.now()

#                 if now > task_timeout:
#                     # 超過時間，更新指令狀態
#                     cmd.cmd_status = CMDStatus.FAILED
#                     update_cmd_status_by_cmd(cmd=cmd)
                    
#                 else:
#                     # 分派指令
#                     self.cmd_dispatch(cmd)
#                     print("dispach!!!!!")

#     def app_deal_timeout_cmd(self):
#         try:
#             print(" app_deal_timeout_cmd START !!!!!!!!")
#             cmds = select_cmd_info(cmd_status=CMDStatus.DOING)

#             if cmds:
#                 for cmd in cmds:
#                     elapsed_time = datetime.now() - cmd.updated_time
#                     print(elapsed_time)
#                     if(elapsed_time > timedelta(minutes=10)):
#                         cmd.cmd_status = CMDStatus.FAILED
#                         result = update_cmd_status_by_cmd(cmd)

#         except BaseException as e:
#             trace_error(e)
#             return False



# # CMD 相關函式: 6 個
# ##新增指令到app_cmd_info
# def insert_cmd_info(cmd):
#     try:
#         config = configparser.ConfigParser()
#         config.read(ConfigEnum.FILE_NAME.value)

#         # ROLE = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_ROLE.value]
#         # GATEWAY_ID = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_GATEWAY_ID.value]
#         # SERVER_ID = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_SERVER_ID.value]

#         # if ROLE == "Server":
#         #     topic = SERVER_ID + "/to/" + GATEWAY_ID
#         # else:
#         #     topic = SERVER_ID + "/from/" + GATEWAY_ID

#         # mqtt_task.topic = topic

#         if cmd.cmd_sn != 0:
#             sql = (
#                 "INSERT INTO `app_cmd_info` (`cmd_sn`, `cmd_type`, "
#                 "`cmd_status`, `cmd_timeout`, `cmd_priority`, "
#                 "`content`, `created_time`, `source`,`destination`) "
#                 "VALUES ('{0}', '{1}', "
#                 "'{2}', '{3}', '{4}', "
#                 "'{5}', '{6}', '{7}', '{8}') "
#                 "ON DUPLICATE KEY "
#                 "UPDATE `app_cmd_info`.`created_time` = VALUES (`app_cmd_info`.`created_time`) "
#             ).format(
#                 cmd.cmd_sn, cmd.cmd_type.value,
#                 cmd.cmd_status.value, cmd.cmd_timeout, cmd.cmd_priority,
#                 cmd.content, datetime.now(),cmd.source.value,cmd.destination.value)
#         else:
#             sql = (
#                     "INSERT INTO `app_cmd_info` (`cmd_type`, "
#                     "`cmd_status`, `cmd_timeout`, `cmd_priority`, "
#                     "`content`, `created_time`, `source`,`destination`) "
#                     "VALUES ('{0}', "
#                     "'{1}', '{2}', '{3}', "
#                     "'{4}', '{5}', '{6}', '{7}') "
#                     "ON DUPLICATE KEY "
#                     "UPDATE `app_cmd_info`.`created_time` = VALUES (`app_cmd_info`.`created_time`) "
#                 ).format(
#                     cmd.cmd_type.value,cmd.cmd_status.value, cmd.cmd_timeout, cmd.cmd_priority,
#                     cmd.content, datetime.now(),cmd.source.value,cmd.destination.value)
        
#         dbh = MySQL()
#         print(sql)
#         result = dbh.execute(sql)
#         dbh.close()

#         if not result:
#             raise Exception(get_function_name(), " Fail")

#         cmd.cmd_sn = result.get('sn')

#         # insert_mqtt_task_log_by_mqtt_task(
#         #     mqtt_task=mqtt_task)

#         return cmd.cmd_sn
#     except BaseException as e:
#         trace_error(e)

# ##刪除指令狀態為terminated的指令
# def delete_cmd_where_terminated():
#     try:
#         sql = (
#             "DELETE FROM `app_cmd_info` "
#             "WHERE `cmd_status` = '{0}' "
#         ).format(CMDStatus.TERMINATED.value)

#         dbh = MySQL()
#         print(sql)
#         result = dbh.execute(sql)
#         print(result)
#         dbh.close()

#         if not result:
#             raise Exception(get_function_name(), " Fail")

#         return result
#     except BaseException as e:
#         trace_error(e)

# # 更新指令的狀態
# def update_cmd_status_by_cmd(cmd: CMD = None):
#     try:
#         now_time = datetime.now().astimezone()
#         spend_time = now_time.replace(
#             tzinfo=None) - cmd.created_time.replace(tzinfo=None)
#         cmd.updated_time = now_time

#         if not cmd:
#             raise Exception("CMD None", get_function_name(), " Fail")

#         if type(cmd.cmd_sn) == list:
#            sql = (
#                 "UPDATE `app_cmd_info` "
#                 "SET `cmd_status` = '{0}', `updated_time` = '{1}' "
#                 "WHERE `cmd_sn` = '{2}' "
#             ).format(cmd.cmd_status.value, cmd.updated_time.replace(tzinfo=None), list_to_tuple_string(cmd.cmd_sn))
#         else:
#             sql = (
#                 "UPDATE `app_cmd_info` "
#                 "SET `cmd_status` = '{0}', `updated_time` = '{1}' "
#                 "WHERE `cmd_sn` = '{2}' "
#             ).format(cmd.cmd_status.value, cmd.updated_time.replace(tzinfo=None), cmd.cmd_sn)

#         dbh = MySQL()
#         print(sql)
#         result = dbh.execute(sql)
#         dbh.close()
#         # print(result)

#         if not result:
#             raise Exception(get_function_name(), " Fail")


#         return result
#     except BaseException as e:
#         trace_error(e)


# # 更新指令的content
# def update_cmd_content(cmd: CMD = None):
#     try:
#         cmd.content = transfer_payload_type(
#             cmd.content, to_type=str)
#         cmd.updated_time = datetime.now().astimezone()
  
#         sql = (
#             "UPDATE `app_cmd_info` "
#             "SET `content`= '{0}', `updated_time` = '{1}' "
#             "WHERE `cmd_sn` = '{2}' "
#         ).format(cmd.content, cmd.updated_time, cmd.cmd_sn)

#         dbh = MySQL()
#         print(sql)
#         result = dbh.execute(sql)
#         dbh.close()
#         print(result)

#         if not result:
#             raise Exception(get_function_name(), " Fail")


#         return result
#     except BaseException as e:
#         trace_error(e)

# #  查找指令的資料
# def select_cmd_info(
#         cmd_sn_list=None,
#         started_time=None,
#         finished_time=None,
#         cmd_type: CMDType = None,
#         cmd_status: CMDStatus = None,
# ) -> Optional[list]:
#     try:
#         compose_list = []

#         if cmd_sn_list is not None:
#             cmd_sn_tuple_str = list_to_tuple_string(cmd_sn_list)
#             compose_list.append("cmd_sn IN {}".format(cmd_sn_tuple_str))


#         if cmd_type is not None:
#             compose_list.append("cmd_type = '{}'".format(cmd_type.value))

#         if cmd_status is not None:
#             compose_list.append(
#                 "cmd_status = '{}' ".format(cmd_status.value))

#         if started_time is not None and finished_time is not None:
#             compose_list.append("(`updated_time` between {} and {})".format(
#                 ymdHMS_format_to_string(started_time),
#                 ymdHMS_format_to_string(finished_time)
#             ))

#         sql = "SELECT * FROM `app_cmd_info` WHERE "
#         sql += ' AND '.join(compose_list)

#         dbh = MySQL()
#         results = dbh.query(sql)
#         dbh.close()

#         cmds = []
#         if not results:
#             return None

#         for result in results:
#             print("result",result)
#             cmds.append(
#                 CMD(
#                     cmd_sn=result.get('cmd_sn'),
#                     cmd_type=CMDType(result.get('cmd_type')),
#                     cmd_status=CMDStatus(result.get('cmd_status')),
#                     cmd_timeout=result.get('cmd_timeout'),
#                     cmd_priority=result.get('cmd_priority'),
#                     created_time=result.get('created_time'),
#                     updated_time=result.get('updated_time'),
#                     content=json.loads(result.get('content')),
#                 )
#             )

#         return cmds
#     except BaseException as e:
#         trace_error(e)

# def delete_cmd_info(cmd: CMD):
#     try:
#         sql = (
#             "DELETE FROM `app_cmd_info` "
#             "WHERE `cmd_sn` = '{0}' "
#             "AND `cmd_type` = '{1}' "
#             "AND `cmd_status` = '{2}' "
#         ).format(cmd.cmd_sn, cmd.cmd_type.value, cmd.cmd_status.value)

#         dbh = MySQL()
#         print(sql)
#         result = dbh.execute(sql)
#         print(result)
#         dbh.close()

#         if not result:
#             raise Exception(get_function_name(), " Fail")

#         return result
#     except BaseException as e:
#         trace_error(e)