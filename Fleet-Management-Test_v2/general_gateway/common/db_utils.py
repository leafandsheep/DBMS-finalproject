import configparser
import json
import uuid
from datetime import datetime
from typing import Optional

from general_gateway.common.datetime_utils import ymdHMS_format_to_string
from general_gateway.common.mqtt_payload_util import transfer_payload_type
from general_gateway.common.payload_format_util import write_task_payload
from general_gateway.common.trace_error_util import trace_error, get_function_name
from general_gateway.models.enum.config_enum import ConfigEnum
from general_gateway.models.enum.message_enum import MessageType, MessageDirection, MessageStatus
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.models.general.mqtt_device import MQTTDevice
from general_gateway.models.general.mqtt_message import MQTTMessage
from general_gateway.models.general.mqtt_task import MQTTTask
from general_gateway.models.mysql import MySQL


"""
list_to_tuple:
"""


def list_to_tuple_string(list_data):
    try:
        if not list_data:
            task_tuple_str = "('')"
        elif len(list_data) == 1:
            task_tuple_str = str(tuple(list_data[:]))
            task_tuple_str = task_tuple_str.replace(",", "")
        else:
            task_tuple_str = str(tuple(list_data[:]))

        return task_tuple_str
    except BaseException as e:
        trace_error(e)


"""
mqtt_message:
"""


def add_to_mqtt_message(
        gateway_id,
        message_id="",
        priority: int = 2,
        gateway_sn: int = 0,
        task_sn: int = 0,
        is_publish: bool = True,
        is_need_ack: bool = False,
        message_type: MessageType = MessageType.REQUEST,
        payload="",
        qos=0, is_retain=0, session_id=1, mqtt_task: MQTTTask = None,
        direction=MessageDirection.FROM,
        schedule_time=None
):
    try:
        config = configparser.ConfigParser()
        config.read(ConfigEnum.FILE_NAME.value)
        SERVER_ID = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_SERVER_ID.value]

        message_id = str(uuid.uuid4()) if message_id == "" else message_id
        topic = SERVER_ID + "/" + direction.value + "/" + gateway_id

        payload = write_task_payload(
            message_id=message_id,
            message_type=message_type,
            is_need_ack=is_need_ack,
            mqtt_task=mqtt_task
        )

        # print()
        # print("===>Payload:")
        # print(payload)

        # if not check_topic(topic):
        #     raise Exception("Topic Format Error")

        # if not check_payload(payload):
        #     raise Exception("Payload Format Error")

        if payload:
            message_id = payload.get('header').get('message_id')

        timestamp = payload.get('header').get('message_timestamp')

        if not schedule_time:
            schedule_time = timestamp

        payload = transfer_payload_type(payload, to_type=str)

        # if is_need_ack:
        #     is_need_ack_value = 1
        # else:
        #     is_need_ack_value = 0

        # 新增處理 Upsert 的方式
        sql = (
            "INSERT INTO `mqtt_message` ("
            "`session_sn`, `message_id`, "
            "`priority`, `schedule_time`, `is_publish`, "
            "`gateway_sn`, `task_sn`, "
            "`topic`, `payload`, "
            "`message_type`, `message_status`, "
            "`qos`, `is_retain`, "
            "`is_need_ack`, `timestamp`"
            ") VALUES ('{0}', '{1}', "
            "{2}, '{3}', {4},"
            "'{5}', '{6}', "
            "'{7}', '{8}', "
            "{9}, {10}, "
            "{11}, {12}, "
            "{13}, '{14}') "
            "ON DUPLICATE KEY "
            "UPDATE `mqtt_message`.`message_status` = VALUES (`mqtt_message`.`message_status`) "
        ).format(
            session_id, message_id,
            int(priority), schedule_time, int(is_publish),
            gateway_sn, task_sn,
            topic, payload,
            message_type.value, MessageStatus.UNSENT.value,
            qos, is_retain,
            int(is_need_ack), timestamp
        )

        dbh = MySQL()
        result = dbh.execute(sql)
        # print(result)

        if not result:
            raise Exception(get_function_name(), " Fail")

        mqtt_message = MQTTMessage(
            message_id=message_id,
            is_publish=is_publish,
            session_sn=session_id,
            gateway_sn=gateway_sn,
            task_sn=task_sn,
            topic=topic,
            payload=payload,
            message_type=message_type,
            message_status=MessageStatus.UNSENT,
            qos=qos,
            is_retain=False,
            is_need_ack=is_need_ack,
            timestamp=timestamp
        )

        insert_app_message_log(mqtt_message)
        # insert_msg_send_receive(mqtt_message)

        return result
    except BaseException as e:
        trace_error(e)


def update_mqtt_message_status_by_message_id(message_id, status=MessageStatus.UNSENT):
    try:
        sql = (
            "UPDATE `mqtt_message` "
            "SET `message_status`= '{0}' "
            "WHERE `message_id` = '{1}' "
        ).format(status.value, message_id)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        # if result.get('result'):
        #     print("message_id:", message_id, "已更新 (發出訊息)")
        return result
    except BaseException as e:
        trace_error(e)


def delete_DONE_mqtt_message():
    try:
        sql = (
            "DELETE FROM `mqtt_message` "
            "WHERE `message_status` = '{0}' "
        ).format(MessageStatus.DONE.value)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result

    except BaseException as e:
        trace_error(e)

def delete_FAILED_mqtt_message():
    try:
        sql = (
            "DELETE FROM `mqtt_message` "
            "WHERE `message_status` = '{0}' "
        ).format(MessageStatus.FAILED.value)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result

    except BaseException as e:
        trace_error(e)

def select_mqtt_message_by_message_id(message_id):
    try:
        sql = (
            "SELECT * FROM `mqtt_message` "
            "WHERE `message_id` = '{0}' "
        ).format(message_id)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        mqtt_message = MQTTMessage()
        for result in results:
            mqtt_message.message_sn = result.get('message_sn')
            mqtt_message.message_id = result.get('message_id')
            mqtt_message.topic = result.get('topic')
            mqtt_message.payload = result.get('payload')
            mqtt_message.message_type = result.get('message_type')
            mqtt_message.message_status = result.get('message_status')
            mqtt_message.is_need_ack = result.get('is_need_ack')

        return mqtt_message
    except BaseException as e:
        trace_error(e)
        return None

def select_message_from_message_log(message_id):
    try:
        sql = (
            "SELECT * FROM `mqtt_message_log` "
            "WHERE `message_id` = '{0}' "
        ).format(message_id)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        mqtt_message = MQTTMessage()
        for result in results:
            mqtt_message.message_sn = result.get('message_sn')
            mqtt_message.message_id = result.get('message_id')
            mqtt_message.topic = result.get('topic')
            mqtt_message.payload = result.get('payload')
            mqtt_message.message_type = result.get('message_type')
            mqtt_message.message_status = result.get('message_status')
            mqtt_message.is_need_ack = result.get('is_need_ack')

        return mqtt_message
    except BaseException as e:
        trace_error(e)
        return None


"""
mqtt_task:
"""

def select_mqtt_task_by_task_status(task_status: TaskStatus):
    try:
        sql = (
            "SELECT * "
            "FROM `mqtt_task` "
            "WHERE `task_status` = '{0}' "
        ).format(task_status.value)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results

    except BaseException as e:
        trace_error(e)
        return False


def select_mqtt_task_by_task_status(task_status: TaskStatus):
    try:
        sql = (
            "SELECT * "
            "FROM `mqtt_task` "
            "WHERE `task_status` = '{0}' "
        ).format(task_status.value)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results

    except BaseException as e:
        trace_error(e)
        return False


def insert_mqtt_task(mqtt_task):
    try:

        config = configparser.ConfigParser()
        config.read(ConfigEnum.FILE_NAME.value)

        ROLE = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_ROLE.value]
        GATEWAY_ID = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_GATEWAY_ID.value]
        SERVER_ID = config[ConfigEnum.BASIC.value][ConfigEnum.BASIC_SERVER_ID.value]

        if ROLE == "Server":
            topic = SERVER_ID + "/to/" + GATEWAY_ID
        else:
            topic = SERVER_ID + "/from/" + GATEWAY_ID

        mqtt_task.topic = topic

        if mqtt_task.task_sn != 0:
            sql = (
                "INSERT INTO `mqtt_task` (`task_sn`, `gateway_sn`, `task_id`, `task_type`, "
                "`task_status`, `task_timeout`, `task_priority`, "
                "`topic`, `content`, `created_time`) "
                "VALUES ('{0}', '{1}', '{2}', '{3}', "
                "'{4}', '{5}', '{6}', "
                "'{7}', '{8}', '{9}') "
                "ON DUPLICATE KEY "
                "UPDATE `mqtt_task`.`created_time` = VALUES (`mqtt_task`.`created_time`) "
            ).format(
                mqtt_task.task_sn, mqtt_task.gateway_sn, mqtt_task.task_id, mqtt_task.task_type.value,
                mqtt_task.task_status.value, mqtt_task.task_timeout, mqtt_task.task_priority,
                topic, mqtt_task.content, datetime.now())
        else:
            if mqtt_task.gateway_sn != 0:
                sql = (
                    "INSERT INTO `mqtt_task` (`gateway_sn`, `task_type`, `task_id`, "
                    "`task_status`, `task_timeout`, `task_priority`, "
                    "`topic`, `content`, `created_time`) "
                    "VALUES ('{0}', '{1}', '{2}', "
                    "'{3}', '{4}', '{5}', "
                    "'{6}', '{7}', '{8}') "
                    "ON DUPLICATE KEY "
                    "UPDATE `mqtt_task`.`created_time` = VALUES (`mqtt_task`.`created_time`) "
                ).format(
                    mqtt_task.gateway_sn, mqtt_task.task_type.value, mqtt_task.task_id,
                    mqtt_task.task_status.value, mqtt_task.task_timeout, mqtt_task.task_priority,
                    topic, mqtt_task.content, datetime.now())
            else:
                sql = (
                    "INSERT INTO `mqtt_task` (`task_type`, `task_id`, "
                    "`task_status`, `task_timeout`, `task_priority`, "
                    "`topic`, `content`, `created_time`) "
                    "VALUES ('{0}', '{1}', '{2}', "
                    "'{3}', '{4}', '{5}', "
                    "'{6}', '{7}') "
                ).format(
                    mqtt_task.task_type.value, mqtt_task.task_id,
                    mqtt_task.task_status.value, mqtt_task.task_timeout, mqtt_task.task_priority,
                    topic, mqtt_task.content, datetime.now())

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        mqtt_task.task_sn = result.get('sn')

        insert_mqtt_task_log_by_mqtt_task(
            mqtt_task=mqtt_task)

        return mqtt_task.task_sn
    except BaseException as e:
        trace_error(e)


def update_mqtt_task_status_by_mqtt_task(mqtt_task: MQTTTask = None):
    try:
        now_time = datetime.now().astimezone()
        spend_time = now_time.replace(
            tzinfo=None) - mqtt_task.created_time.replace(tzinfo=None)
        mqtt_task.updated_time = now_time

        if not mqtt_task:
            raise Exception("MQTT_Task None", get_function_name(), " Fail")

        if type(mqtt_task.task_sn) == list:
            sql = (
                "UPDATE `mqtt_task` "
                "SET `task_status` = '{0}', `updated_time` = '{1}' "
                "WHERE `task_sn` IN {2} "
                "AND `gateway_sn` = '{3}' "
            ).format(mqtt_task.task_status.value, mqtt_task.updated_time.replace(tzinfo=None), list_to_tuple_string(mqtt_task.task_sn), mqtt_task.gateway_sn)
        else:
            sql = (
                "UPDATE `mqtt_task` "
                "SET `task_status` = {0}, `updated_time` = '{1}' "
                "WHERE `task_sn` = '{2}' "
                "AND `gateway_sn` = '{3}' "
            ).format(mqtt_task.task_status.value, mqtt_task.updated_time.replace(tzinfo=None), mqtt_task.task_sn, mqtt_task.gateway_sn)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        dbh.close()
        # print(result)

        if not result:
            raise Exception(get_function_name(), " Fail")

        insert_mqtt_task_log_by_mqtt_task(mqtt_task=mqtt_task)

        return result
    except BaseException as e:
        trace_error(e)


def update_mqtt_task_content(mqtt_task):
    try:
        mqtt_task.content = transfer_payload_type(
            mqtt_task.content, to_type=str)
        mqtt_task.updated_time = datetime.now().astimezone()

        if mqtt_task.gateway_sn != 0:
            sql = (
                "UPDATE `mqtt_task` "
                "SET `content`= '{0}', `updated_time` = '{1}' "
                "WHERE `task_sn` = '{2}' AND `gateway_sn` = '{3}' "
            ).format(mqtt_task.content, mqtt_task.updated_time, mqtt_task.task_sn, mqtt_task.gateway_sn)
        else:
            sql = (
                "UPDATE `mqtt_task` "
                "SET `content`= '{0}', `updated_time` = '{1}' "
                "WHERE `task_sn` = '{2}' "
            ).format(mqtt_task.content, mqtt_task.updated_time, mqtt_task.task_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        dbh.close()
        print(result)

        if not result:
            raise Exception(get_function_name(), " Fail")

        update_app_task_information_content(mqtt_task=mqtt_task)
        insert_mqtt_task_log_by_mqtt_task(mqtt_task=mqtt_task)

        return result
    except BaseException as e:
        trace_error(e)


def update_app_task_information_content(mqtt_task):
    try:
        if mqtt_task.gateway_sn != 0:
            sql = (
                "UPDATE `mqtt_task` "
                "SET `content`= '{0}', `updated_time` = '{1}' "
                "WHERE `task_sn` = '{2}' AND `gateway_sn` = '{3}' "
            ).format(mqtt_task.content, mqtt_task.updated_time, mqtt_task.task_sn, mqtt_task.gateway_sn)
        else:
            sql = (
                "UPDATE `mqtt_task` "
                "SET `content`= '{0}', `updated_time` = '{1}' "
                "WHERE `task_sn` = '{2}' "
            ).format(mqtt_task.content, mqtt_task.updated_time, mqtt_task.task_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        dbh.close()

        print(result)

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)


def delete_mqtt_task_where_terminated():
    try:
        sql = (
            "DELETE FROM `mqtt_task` "
            "WHERE `task_status` = '{0}' "
        ).format(TaskStatus.TERMINATED.value)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def delete_mqtt_task_where_failed():
    try:
        sql = (
            "DELETE FROM `mqtt_task` "
            "WHERE `task_status` = '{0}' "
        ).format(TaskStatus.FAILED.value)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def select_mqtt_tasks(
        task_sn_list=None,
        task_id_list=None,
        gateway_sn=None,
        started_time=None,
        finished_time=None,
        task_type = None,
        task_status: TaskStatus = None,
) -> Optional[list]:
    try:
        compose_list = []

        if task_sn_list is not None:
            task_sn_tuple_str = list_to_tuple_string(task_sn_list)
            compose_list.append("task_sn IN {}".format(task_sn_tuple_str))

        if task_id_list is not None:
            task_id_tuple_str = list_to_tuple_string(task_id_list)
            compose_list.append("task_id IN {}".format(task_id_tuple_str))

        if gateway_sn is not None:
            compose_list.append("gateway_sn = '{}'".format(gateway_sn))

        if task_type is not None:
            compose_list.append("task_type = '{}'".format(task_type.value))

        if task_status is not None:
            compose_list.append(
                "task_status = '{}' ".format(task_status.value))

        if started_time is not None and finished_time is not None:
            compose_list.append("(`updated_time` between {} and {})".format(
                ymdHMS_format_to_string(started_time),
                ymdHMS_format_to_string(finished_time)
            ))

        sql = "SELECT * FROM `mqtt_task` WHERE "
        sql += ' AND '.join(compose_list)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        mqtt_tasks = []
        if not results:
            return None

        for result in results:
            mqtt_tasks.append(
                MQTTTask(
                    task_sn=result.get('task_sn'),
                    task_id=result.get('task_id'),
                    gateway_sn=result.get('gateway_sn'),
                    task_type=result.get('task_type'),
                    task_status=TaskStatus(result.get('task_status')),
                    task_timeout=result.get('task_timeout'),
                    task_priority=result.get('task_priority'),
                    created_time=result.get('created_time'),
                    updated_time=result.get('updated_time'),
                    content=json.loads(result.get('content')),
                )
            )

        return mqtt_tasks
    except BaseException as e:
        trace_error(e)


def select_mqtt_task_and_app_item(task_type=None, task_status: tuple = None):
    try:
        compose_list = []

        if task_type is not None:
            compose_list.append(
                " `task_type` = '{0}' ".format(task_type.value))

        if task_status is not None:
            compose_list.append(" `task_status` IN {0} ".format(task_status))

        sql = "SELECT T.`task_sn`, T.`task_id`, T.`task_status`, T.`created_time`, I_T.`item_sn`," \
              "I.`item_id`, I.`item_name`, I_T.`quantity` " \
              "FROM `mqtt_task` AS T, `app_items_in_the_task` AS I_T, `app_item` AS I " \
              "WHERE "
        sql += ' AND '.join(compose_list)
        sql += " AND T.`task_sn` = I_T.`task_sn` " \
               "AND I.`item_sn` = I_T.`item_sn` " \
               "ORDER BY T.`task_sn` "

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        return results
    except BaseException as e:
        trace_error(e)


# def select_mqtt_task_by_task_sn(task_sn):
#     try:
#         mqtt_task = MQTTTask(task_sn=task_sn)
#         sql = (
#             "SELECT * FROM `mqtt_task` "
#             "WHERE `task_sn` = '{0}' "
#         ).format(mqtt_task.task_sn)
#
#         dbh = MySQL()
#         task_result = dbh.query(sql)
#
#         if task_result:
#             for result in task_result:
#                 mqtt_task.task_sn = result.get('task_sn')
#                 mqtt_task.task_id = result.get('task_id')
#                 mqtt_task.task_type = TaskType(result.get('task_type'))
#                 mqtt_task.task_status = TaskStatus(result.get('task_status'))
#                 mqtt_task.content = result.get('content')
#                 mqtt_task.task_timeout = result.get('task_timeout')
#                 mqtt_task.task_priority = result.get('task_priority')
#                 mqtt_task.created_time = datetime_format(
#                     result.get('created_time'),
#                     from_datetime_type=DateTimeType.YMDHMS_FORMAT,
#                     to_datetime_type=DateTimeType.ISO8601_FORMAT
#                 )
#
#                 if mqtt_task.updated_time:
#                     mqtt_task.updated_time = datetime_format(
#                         result.get('updated_time'),
#                         from_datetime_type=DateTimeType.YMDHMS_FORMAT,
#                         to_datetime_type=DateTimeType.ISO8601_FORMAT
#                     )
#
#         sql = (
#             "SELECT * FROM `app_item`, `app_items_in_the_task` "
#             "WHERE `app_item`.`item_sn` = `app_items_in_the_task`.`item_sn` "
#             "AND `app_items_in_the_task`.`task_sn` = '{0}' "
#         ).format(mqtt_task.task_sn)
#         print(sql)
#         item_result = dbh.query(sql)
#
#         if item_result:
#             for result in item_result:
#                 item_sn = result.get('item_sn')
#                 app_item = AppItem(
#                     task_sn=mqtt_task.task_sn,
#                     gateway_sn=mqtt_task.gateway_sn,
#                     item_sn=item_sn,
#                     item_id=result.get('item_id'),
#                     item_name=result.get('item_name'),
#                     quantity=result.get('quantity')
#                 )
#                 sql = (
#                     "SELECT * FROM `app_item`, `app_item_rfid` "
#                     "WHERE `app_item`.`item_sn` = `app_item_rfid`.`item_sn` "
#                     "AND `app_item`.`item_sn` = '{0}' "
#                 ).format(item_sn)
#
#                 print(sql)
#                 item_rfid_result = dbh.query(sql)
#
#                 if item_rfid_result:
#                     for result in item_rfid_result:
#                         app_item_RFID = AppItemRFID(
#                             item_sn=item_sn,
#                             rfid=result.get('rfid'),
#                             rfid_status=result.get('rfid_status'),
#                             rfid_location=result.get('rfid_location'),
#                             created_time=datetime_format(
#                                 result.get('created_time'),
#                                 from_datetime_type=DateTimeType.YMDHMS_FORMAT,
#                                 to_datetime_type=DateTimeType.ISO8601_FORMAT
#                             ),
#                             last_inventory_time=datetime_format(
#                                 result.get('last_inventory_time'),
#                                 from_datetime_type=DateTimeType.YMDHMS_FORMAT,
#                                 to_datetime_type=DateTimeType.ISO8601_FORMAT
#                             )
#                         )
#                     app_item.app_item_rfids.append(app_item_RFID)
#                 mqtt_task.app_items.append(app_item)
#
#         sql = (
#             "SELECT * FROM `app_inventory_record` "
#             "WHERE `task_sn` = '{0}' "
#         ).format(mqtt_task.task_sn)
#         print(sql)
#         inventory_record_result = dbh.query(sql)
#         dbh.close()
#
#         if inventory_record_result:
#             for result in inventory_record_result:
#                 app_inventory_record = AppInventoryRecord(
#                     task_sn=mqtt_task.task_sn,
#                     rfid=result.get('rfid'),
#                     created_time=datetime_format(
#                         result.get('created_time'),
#                         from_datetime_type=DateTimeType.YMDHMS_FORMAT,
#                         to_datetime_type=DateTimeType.ISO8601_FORMAT
#                     )
#                 )
#                 mqtt_task.app_inventory_records.append(app_inventory_record)
#
#         return mqtt_task
#     except BaseException as e:
#         trace_error(e)
#         return mqtt_task


def delete_mqtt_task(mqtt_task: MQTTTask):
    try:
        sql = (
            "DELETE FROM `mqtt_task` "
            "WHERE `task_sn` = '{0}' "
            "AND `task_type` = '{1}' "
            "AND `task_status` = '{2}' "
        ).format(mqtt_task.task_sn, mqtt_task.task_type.value, mqtt_task.task_status.value)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)


def insert_mqtt_task_log_by_mqtt_task(mqtt_task: MQTTTask):
    try:
        mqtt_task.content = transfer_payload_type(
            mqtt_task.content, to_type=str)

        if type(mqtt_task.task_sn) == list:
            sql = (
                "INSERT INTO `mqtt_task_log` "
                "(`task_sn`, `gateway_sn`, `task_status`, `content`, `updated_time`) "
                "VALUES "
            )
            # print(mqtt_task.task_sn)
            # print(type(mqtt_task.task_sn))
            for task_sn in mqtt_task.task_sn:
                sql += (
                    "('{0}', '{1}', '{2}', '{3}', '{4}'),"
                ).format(task_sn, mqtt_task.gateway_sn,
                         mqtt_task.task_status.value, mqtt_task.content, mqtt_task.updated_time.replace(tzinfo=None))
            sql = sql[:-1]

        # Doorkeeper:接收訊息
        elif mqtt_task.gateway_sn:
            if mqtt_task.updated_time:
                sql = (
                    "INSERT INTO `mqtt_task_log` "
                    "(`task_sn`, `gateway_sn`, `task_status`, `content`, `updated_time`) "
                    "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') "
                ).format(mqtt_task.task_sn, mqtt_task.gateway_sn, mqtt_task.task_status.value,
                         mqtt_task.content, mqtt_task.updated_time.replace(tzinfo=None))
            # 剛製單，未有 updated_time
            else:
                sql = (
                    "INSERT INTO `mqtt_task_log` "
                    "(`task_sn`, `gateway_sn`, `task_status`, `content`, `updated_time`) "
                    "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') "
                ).format(mqtt_task.task_sn, mqtt_task.gateway_sn, mqtt_task.task_status.value,
                         mqtt_task.content, mqtt_task.created_time.replace(tzinfo=None))
        # Server 製單，未派發
        else:
            sql = (
                "INSERT INTO `mqtt_task_log` "
                "(`task_sn`, `gateway_sn`, `task_status`, `content`, `updated_time`) "
                "VALUES ('{0}', {1}, '{2}', '{3}', '{4}') "
            ).format(mqtt_task.task_sn, "NULL", mqtt_task.task_status.value,
                     mqtt_task.content, mqtt_task.created_time.replace(tzinfo=None))

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result

    except BaseException as e:
        trace_error(e)

"""
mqtt_message_log:
"""


def insert_app_message_log(message: MQTTMessage):
    try:
        sql = (
            "INSERT INTO `mqtt_message_log` ("
            "`session_sn`, `message_id`, `is_publish`, "
            "`gateway_sn`, `task_sn`, "
            "`topic`, `payload`, "
            "`message_type`, `message_status`, "
            "`qos`, `is_retain`, "
            "`is_need_ack`, `timestamp`"
            ") VALUES ('{0}', '{1}', {2}, "
            "'{3}', '{4}', "
            "'{5}', '{6}', "
            "{7}, {8}, "
            "{9}, {10}, "
            "{11}, '{12}') "
            "ON DUPLICATE KEY "
            "UPDATE `mqtt_message_log`.`message_status` = VALUES (`mqtt_message_log`.`message_status`) "
        ).format(
            message.session_sn, message.message_id, int(message.is_publish),
            message.gateway_sn, message.task_sn,
            message.topic, message.payload,
            message.message_type.value, message.message_status.value,
            message.qos, int(message.is_retain),
            int(message.is_need_ack), message.timestamp
        )

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
        return False


"""
mqtt_gateway:
"""


def get_mqtt_gateway_by_gateway_id(gateway_id):
    pass


"""
matt_device
"""


def insert_mqtt_device(mqtt_device: MQTTDevice):
    try:
        sql = (
            "INSERT INTO `mqtt_device` (`gateway_sn`, `device_status`, `device_meta`, `created_time`) "
            "VALUES ({0}, {1}, '{2}', '{3}') "
            "ON DUPLICATE KEY "
            "UPDATE `mqtt_device`.`updated_time` = VALUES (`mqtt_device`.`updated_time`) "
        ).format(
            mqtt_device.gateway_sn, mqtt_device.device_status, mqtt_device.device_meta, mqtt_device.created_time
        )
       

        dbh = MySQL()
        result = dbh.execute(sql)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
        return False

# 20240629 record message transfer time
def record_message_transfer_time(message_id, start_time, end_time):
    try:
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        duration_in_seconds = abs((end_time - start_time).total_seconds())  # 計算時間差並轉換為秒

        sql = (
            "INSERT INTO `time_measurement` (`message_id`, `start_time`, `end_time`, `duration`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}')"
        ).format(message_id, start_time_str, end_time_str, duration_in_seconds)

        dbh = MySQL()
        result = dbh.execute(sql)  # 使用包含所有參數的單個調用
        dbh.close()

        if not result:
            raise Exception("Failed to record time measurement for message_id: " + message_id)

        if result.get('result'):
            print("Time measurement recorded for message_id:", message_id)

        return result
    except Exception as e:
        print(f"An error occurred: {e}")
    
'''
20240614 mqtt_message real time info
'''

def insert_msg_send_receive(message: MQTTMessage):
    try:
        sql = (
            "INSERT INTO `msg_send_receive` ("
            "`message_id`, `is_publish`, "
            "`gateway_sn`, `task_sn`, "
            "`topic`, `payload`, "
            "`message_type`, `message_status`, "
            "`is_need_ack`, `timestamp`"
            ") VALUES ('{0}', {1}, "
            "'{2}', '{3}', "
            "'{4}', '{5}', "
            "{6}, {7}, "
            "{8}, '{9}') "
            "ON DUPLICATE KEY "
            "UPDATE `msg_send_receive`.`message_status` = VALUES (`msg_send_receive`.`message_status`) "
        ).format(
            message.message_id, int(message.is_publish),
            message.gateway_sn, message.task_sn,
            message.topic, message.payload,
            message.message_type.value, message.message_status.value,
            int(message.is_need_ack), message.timestamp
        )

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
        return False

"""
20240614 delete real time mqtt message
"""

def delete_real_time_mqtt_message():
    try:
        sql = (
            "DELETE FROM `msg_send_receive` "
            "WHERE `message_status` = '{0}' "
        ).format(MessageStatus.DONE.value)

        dbh = MySQL()
        print(sql)

        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result

    except BaseException as e:
        trace_error(e)

def update_msg_status_by_id(message_id, status=MessageStatus.UNSENT):
    try:
        sql = (
            "UPDATE `msg_send_receive` "
            "SET `message_status`= '{0}' "
            "WHERE `message_id` = '{1}' "
        ).format(status.value, message_id)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
# 20240623 設定待發送訊息上限
def maintain_mqtt_message_table(msg_limit):
    try:
        # 建立 MySQL 連接
        dbh = MySQL()
        
        # Step 1: 計算總訊息數量
        sql_count_total = "SELECT COUNT(*) AS count FROM mqtt_message"
        total_messages = dbh.query(sql_count_total)[0]['count']
        print(f"Total messages: {total_messages}")

        # Step 2: 計算 priority < 2 的訊息數量
        sql_count_priority = "SELECT COUNT(*) AS count FROM mqtt_message WHERE priority < 2"
        priority_messages = dbh.query(sql_count_priority)[0]['count']
        print("Priority < 2 messages: ", priority_messages)

        # Step 3: 計算需要刪除的訊息數量
        delete_count = total_messages - msg_limit
        if delete_count <= 0:
            print("No messages need to be deleted.")
            dbh.close()
            return

        print("Messages to delete: ", delete_count)

        # Step 4: 刪除多餘的 priority >= 2 的訊息
        sql_delete = (
            "DELETE FROM mqtt_message "
            "WHERE message_sn IN ("
            "  SELECT message_sn FROM ("
            "    SELECT message_sn FROM mqtt_message "
            "    WHERE priority >= 2 "
            "    ORDER BY schedule_time ASC "
            "    LIMIT {0}"
            "  ) AS subquery"
            ")"
        ).format(delete_count)
        
        if dbh.execute(sql_delete):
            print(f"Deleted {delete_count} messages successfully.")
        else:
            print("Failed to delete messages.")
        
        dbh.close()

    except Exception as e:
        trace_error(e)

def update_resend_times_by_message_id(message_id, resend_times):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `resend_times`= '{0}' "
            "WHERE `message_id` = '{1}' "
        ).format(resend_times, message_id)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        return result
    except BaseException as e:
        trace_error(e)

def update_message_status_in_messsage_log(message_id, status=MessageStatus.DONE):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `message_status`= '{0}' "
            "WHERE `message_id` = '{1}' "
        ).format(status.value, message_id)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def update_message_log(resend_times = 0, mqtt_message=MQTTMessage):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `payload`= '{0}' , `message_status`= '{1}', "
            "`is_need_ack`= '{2}', `timestamp`= '{3}' , `resend_times`= '{4}' "
            "WHERE `message_id` = '{5}' "
        ).format(
            mqtt_message.payload, mqtt_message.message_status, \
                int(mqtt_message.is_need_ack), mqtt_message.timestamp, resend_times, mqtt_message.message_id
        )

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def update_message_log_without_payload_timestamp(mqtt_message=MQTTMessage):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `message_status`= '{0}', "
            "`is_need_ack`= '{1}' "
            "WHERE `message_id` = '{2}' "
        ).format(
            mqtt_message.message_status, int(mqtt_message.is_need_ack), mqtt_message.message_id
        )

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def update_done_message_in_message_log(mqtt_message=MQTTMessage):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `message_status`= '{0}', "
            "`is_need_ack`= '{1}', `timestamp`= '{2}' "
            "WHERE `message_id` = '{3}' "
        ).format( mqtt_message.message_status, \
                int(mqtt_message.is_need_ack), mqtt_message.timestamp, mqtt_message.message_id
        )

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def update_payload_and_timestamp_in_message_log(mqtt_message=MQTTMessage):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `payload` = '{0}', `timestamp` = '{1}' "
            "WHERE `message_id` = '{2}'"
        ).format(
            mqtt_message.payload, mqtt_message.timestamp, mqtt_message.message_id
        )

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result['result'])
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def update_done_message_in_message_log_only_timestamp(mqtt_message=MQTTMessage):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `timestamp`= '{0}' "
            "WHERE `message_id` = '{1}' "
        ).format(mqtt_message.timestamp, mqtt_message.message_id)

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)

def update_done_message_in_message_log_no_timestamp(mqtt_message=MQTTMessage):
    try:
        sql = (
            "UPDATE `mqtt_message_log` "
            "SET `message_status`= '{0}', "
            "`is_need_ack`= '{1}' "
            "WHERE `message_id` = '{2}' "
        ).format( mqtt_message.message_status, \
                int(mqtt_message.is_need_ack), mqtt_message.message_id
        )

        dbh = MySQL()
        # print(sql)
        result = dbh.execute(sql)
        # print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)