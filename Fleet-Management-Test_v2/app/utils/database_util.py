import json
import os
import uuid
from datetime import datetime
from typing import Optional

from app.data.model.mqtt_gateway import MQTTGateway
from app.data.model.mqtt_message import MQTTMessage
from app.data.model.mqtt_task import MQTTTask

from app.data.enum.message_enum import (MessageDirection,
                                        MessageStatus,
                                        MessageType)
from app.data.enum.task_enum import TaskStatus, TaskType
from app.setting import GATEWAY_ID, ROLE, SERVER_ID
from app.mysql import MySQL

from app.utils.datetime_enum import DateTimeType
from app.utils.datetime_utils import (datetime_format,
                                      iso8601_format_to_string,
                                      string_convert_to_date,
                                      ymdHMS_format_to_string)
from app.utils.mqtt_payload_util import transfer_payload_type
from app.utils.payload_format_util import write_task_payload
from app.utils.trace_error_util import get_function_name, trace_error

"""
experiment:
"""


def insert_experiment_log(task_sn, type_sn, spend_time):
    try:
        sql = (
            "INSERT INTO `app_overhead` "
            "(`task_sn`, `type_sn`, `spend_time`) "
            "VALUES ({0}, {1}, '{2}') "
            "ON DUPLICATE KEY "
            "UPDATE `app_overhead`.`type_sn` = VALUES (`app_overhead`.`type_sn`) "
        ).format(task_sn, type_sn, spend_time)

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
app_message_log:
"""


def insert_app_message_log(message: MQTTMessage):
    try:
        sql = (
            "INSERT INTO `app_message_log` ("
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
            "UPDATE `app_message_log`.`message_status` = VALUES (`app_message_log`.`message_status`) "
        ).format(
            message.session_sn, message.message_id, int(message.is_publish),
            message.gateway_sn, message.task_sn,
            message.topic, message.payload,
            message.message_type.value, message.message_status.value,
            message.qos, int(message.is_retain),
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
mqtt_message:
"""


def add_to_mqtt_message(
        message_id="",
        priority: int = 1,
        gateway_sn: int = 0,
        task_sn: int = 0,
        is_publish: bool = True,
        is_need_ack: bool = False,
        message_type: MessageType = MessageType.REQUEST,
        payload="",
        qos=0, is_retain=0, session_id=1, mqtt_task: MQTTTask = None,
        direction=MessageDirection.FROM, gateway_id=GATEWAY_ID,
        schedule_time=None,
):
    try:
        message_id = str(uuid.uuid4()) if message_id == "" else message_id
        topic = SERVER_ID + "/" + direction.value + "/" + gateway_id

        payload = write_task_payload(
            message_id=message_id,
            message_type=message_type,
            is_need_ack=is_need_ack,
            mqtt_task=mqtt_task
        )

        print()
        print("===>Payload:")
        print(payload)

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
        print()
        print("待發訊息 ===>")
        print(sql)
        result = dbh.execute(sql)
        print(result)

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
        print(sql)
        result = dbh.execute(sql)
        print(result)
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
        print(sql)

        result = dbh.execute(sql)
        print(result)
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
            mqtt_message.publish_message_sn = result.get('publish_message_sn')
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


def insert_mqtt_task(mqtt_task):
    try:
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
        print(sql)
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
        print(sql)
        result = dbh.execute(sql)
        dbh.close()
        print(result)

        if not result:
            raise Exception(get_function_name(), " Fail")

        insert_mqtt_task_log_by_mqtt_task(mqtt_task=mqtt_task)

        return result
    except BaseException as e:
        trace_error(e)


def update_mqtt_task_gateway_sn_by_mqtt_task(mqtt_task: MQTTTask):
    try:
        sql = (
            "UPDATE `mqtt_task` "
            "SET gateway_sn = '{0}', `task_status` = '{1}', `updated_time` = '{2}' "
            "WHERE `task_sn` = '{3}' "
        ).format(mqtt_task.gateway_sn, mqtt_task.task_status.value, mqtt_task.updated_time, mqtt_task.task_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        dbh.close()
        print(result)

        if not result:
            raise Exception(get_function_name(), " Fail")

        insert_mqtt_task_log_by_mqtt_task(
            mqtt_task=mqtt_task)

    except BaseException as e:
        trace_error(e)

def update_mqtt_task_by_task_sn_and_gateway_sn(mqtt_task: MQTTTask):
    try:
        sql = (
            "UPDATE `mqtt_task` "
            "SET `task_id` = '{0}', `task_status`= '{1}', `content` = '{2}', "
            "`created_time` = '{3}', `updated_time` = '{4}' "
            "WHERE `task_sn` = '{5}' "
        ).format(mqtt_task.task_id, mqtt_task.task_status.value, mqtt_task.content,
                 mqtt_task.created_time, mqtt_task.updated_time,
                 mqtt_task.task_sn)

        insert_mqtt_task_log_by_mqtt_task(mqtt_task=mqtt_task)

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

        insert_mqtt_task_log_by_mqtt_task(mqtt_task=mqtt_task)

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


def select_mqtt_tasks(
        task_sn_list=None,
        task_id_list=None,
        gateway_sn=None,
        started_time=None,
        finished_time=None,
        task_type: TaskType = None,
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
                    task_type=TaskType(result.get('task_type')),
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


def select_mqtt_task_by_task_sn(task_sn):
    try:
        mqtt_task = MQTTTask(task_sn=task_sn)
        sql = (
            "SELECT * FROM `mqtt_task` "
            "WHERE `task_sn` = '{0}' "
        ).format(mqtt_task.task_sn)

        dbh = MySQL()
        task_result = dbh.query(sql)

        if task_result:
            for result in task_result:
                mqtt_task.task_sn = result.get('task_sn')
                mqtt_task.task_id = result.get('task_id')
                mqtt_task.task_type = TaskType(result.get('task_type'))
                mqtt_task.task_status = TaskStatus(result.get('task_status'))
                mqtt_task.content = result.get('content')
                mqtt_task.task_timeout = result.get('task_timeout')
                mqtt_task.task_priority = result.get('task_priority')
                mqtt_task.created_time = datetime_format(
                    result.get('created_time'),
                    from_datetime_type=DateTimeType.YMDHMS_FORMAT,
                    to_datetime_type=DateTimeType.ISO8601_FORMAT
                )

                if mqtt_task.updated_time:
                    mqtt_task.updated_time = datetime_format(
                        result.get('updated_time'),
                        from_datetime_type=DateTimeType.YMDHMS_FORMAT,
                        to_datetime_type=DateTimeType.ISO8601_FORMAT
                    )

        sql = (
            "SELECT * FROM `app_item`, `app_items_in_the_task` "
            "WHERE `app_item`.`item_sn` = `app_items_in_the_task`.`item_sn` "
            "AND `app_items_in_the_task`.`task_sn` = '{0}' "
        ).format(mqtt_task.task_sn)
        print(sql)
        item_result = dbh.query(sql)

        if item_result:
            for result in item_result:
                item_sn = result.get('item_sn')
                app_item = AppItem(
                    task_sn=mqtt_task.task_sn,
                    gateway_sn=mqtt_task.gateway_sn,
                    item_sn=item_sn,
                    item_id=result.get('item_id'),
                    item_name=result.get('item_name'),
                    quantity=result.get('quantity')
                )
                sql = (
                    "SELECT * FROM `app_item`, `app_item_rfid` "
                    "WHERE `app_item`.`item_sn` = `app_item_rfid`.`item_sn` "
                    "AND `app_item`.`item_sn` = '{0}' "
                ).format(item_sn)

                print(sql)
                item_rfid_result = dbh.query(sql)

                if item_rfid_result:
                    for result in item_rfid_result:
                        app_item_RFID = AppItemRFID(
                            item_sn=item_sn,
                            rfid=result.get('rfid'),
                            rfid_status=result.get('rfid_status'),
                            rfid_location=result.get('rfid_location'),
                            created_time=datetime_format(
                                result.get('created_time'),
                                from_datetime_type=DateTimeType.YMDHMS_FORMAT,
                                to_datetime_type=DateTimeType.ISO8601_FORMAT
                            ),
                            last_inventory_time=datetime_format(
                                result.get('last_inventory_time'),
                                from_datetime_type=DateTimeType.YMDHMS_FORMAT,
                                to_datetime_type=DateTimeType.ISO8601_FORMAT
                            )
                        )
                    app_item.app_item_rfids.append(app_item_RFID)
                mqtt_task.app_items.append(app_item)

        sql = (
            "SELECT * FROM `app_inventory_record` "
            "WHERE `task_sn` = '{0}' "
        ).format(mqtt_task.task_sn)
        print(sql)
        inventory_record_result = dbh.query(sql)
        dbh.close()

        if inventory_record_result:
            for result in inventory_record_result:
                app_inventory_record = AppInventoryRecord(
                    task_sn=mqtt_task.task_sn,
                    rfid=result.get('rfid'),
                    created_time=datetime_format(
                        result.get('created_time'),
                        from_datetime_type=DateTimeType.YMDHMS_FORMAT,
                        to_datetime_type=DateTimeType.ISO8601_FORMAT
                    )
                )
                mqtt_task.app_inventory_records.append(app_inventory_record)

        return mqtt_task
    except BaseException as e:
        trace_error(e)
        return mqtt_task


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


"""
mqtt_task_log:
"""


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
            print(mqtt_task.task_sn)
            print(type(mqtt_task.task_sn))
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
        print(sql)
        result = dbh.execute(sql)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result

    except BaseException as e:
        trace_error(e)


"""
mqtt_gateway:
"""


def select_mqtt_gateway_by_gateway_sn(gateway_sn):
    try:
        sql = "SELECT * FROM `mqtt_gateway` WHERE `gateway_sn` = '{0}' ".format(
            gateway_sn)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        mqtt_gateway = MQTTGateway()
        if results:
            mqtt_gateway.gateway_sn = results[0].get('gateway_sn')
            mqtt_gateway.gateway_mac_address = results[0].get(
                'gateway_mac_address')
            mqtt_gateway.gateway_name = results[0].get('gateway_name')
            mqtt_gateway.gateway_status = results[0].get('gateway_status')
            mqtt_gateway.created_time = results[0].get('created_time')
            mqtt_gateway.updated_time = results[0].get('updated_time')

        return mqtt_gateway
    except BaseException as e:
        trace_error(e)


def select_mqtt_gateways(
        mac_address=None,
        gateway_status_list=None
):
    try:
        compose_list = []

        if mac_address is not None:
            compose_list.append(
                "gateway_mac_address = '{}'".format(mac_address))

        if gateway_status_list is not None:
            gateway_status_list = [
                gateway_status.value for gateway_status in gateway_status_list]
            if len(gateway_status_list) == 1:
                gateway_status_list_tuple = str(tuple(gateway_status_list[:]))
                gateway_status_list_tuple = gateway_status_list_tuple.replace(
                    ",", "")
            else:
                gateway_status_list_tuple = str(tuple(gateway_status_list[:]))

            compose_list.append("gateway_status IN {} ".format(
                gateway_status_list_tuple))

        sql = "SELECT * FROM `mqtt_gateway` WHERE "
        sql += ' AND '.join(compose_list)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        mqtt_gateways = []
        if results:
            for result in results:
                mqtt_gateways.append(MQTTGateway(
                    gateway_sn=result.get('gateway_sn'),
                    gateway_mac_address=result.get('gateway_mac_address'),
                    gateway_name=result.get('gateway_name'),
                    gateway_status=result.get('gateway_status'),
                    created_time=result.get('created_time'),
                    updated_time=result.get('updated_time')
                ))

        return mqtt_gateways
    except BaseException as e:
        trace_error(e)


"""
app_node:
"""


def select_app_node(gateway_sn: int, node_sn: int):
    try:
        sql = (
            "SELECT `a_n`.`type_sn`, `a_n`.`device_address`, `a_n`.`node_num` "
            "FROM `app_node` AS `a_n` "
            "INNER JOIN `mqtt_gateway` AS `m_q` "
            "ON ( `a_n`.`gateway_sn` = `m_q`.`gateway_sn` ) "
            "WHERE `m_q`.`gateway_sn` = {0} "
            "AND `a_n`.`node_sn` = {1} "
            "LIMIT 1 "
        ).format(gateway_sn, node_sn)

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


def update_app_node(gateway_sn: int, node_sn: int, node_status: int):
    try:
        sql = (
            "UPDATE `app_node` SET `node_status` = {0} "
            "WHERE `gateway_sn` = {1} AND `node_sn` = {2} "
        ).format(node_status, gateway_sn, node_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False

# def update_app_node_adjustment(gateway_sn):
#     try:
#         item_node_list_field = '`nl`.`type_id`, `il`.`node_id`, `il`.`node_state`' if control_type == 'scene' else '`nl`.`type_id`, `il`.`node_id`'

#         item_node_list_table = (
#             "`{}_node_list` AS `il` "
#             "INNER JOIN `node_list` AS `nl` "
#             "ON ( `il`.`node_id` = `nl`.`node_id` "
#             "AND `il`.`gateway_id` = `nl`.`gateway_id` ) "
#         ).format(control_type)

#         sql = (
#             "SELECT {0} "
#             "FROM {1} "
#             "WHERE `il`.`gateway_id` = {2} "
#             "AND `il`.`{3}_id` = {4} "
#         ).format(item_node_list_field, item_node_list_table, gateway_id, control_type, item_id)

#     except Exception as e:
#         trace_error(e)
#         return False


"""
app_group:
"""


def select_app_group(gateway_sn: int, group_sn: int):
    try:
        sql = (
            "SELECT `a_g`.`group_num` "
            "FROM `app_group` AS `a_g` "
            "INNER JOIN `mqtt_gateway` AS `m_q` "
            "ON ( `a_g`.`gateway_sn` = `m_q`.`gateway_sn` ) "
            "WHERE `m_q`.`gateway_sn` = {0} "
            "AND `a_g`.`group_sn` = {1} "
            "LIMIT 1 "
        ).format(gateway_sn, group_sn)

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


def update_app_group(gateway_sn: int, group_sn: int, group_status: int):
    try:
        sql = (
            "UPDATE `app_group` SET `group_status` = {0} "
            "WHERE `gateway_sn` = {1} AND `group_sn` = {2} "
        ).format(group_status, gateway_sn, group_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False


"""
app_group_node:
"""


def select_app_group_node(gateway_sn: int, group_sn: int):
    try:
        sql = (
            "SELECT `a_n`.`node_sn` "
            "FROM `app_node` AS `a_n` "
            "INNER JOIN `app_group_node` AS `a_g_n` "
            "ON ( `a_n`.`gateway_sn` = `a_g_n`.`gateway_sn` "
            "AND `a_n`.`node_sn` = `a_g_n`.`node_sn` ) "
            "WHERE `a_g_n`.`gateway_sn` = {0} "
            "AND `a_g_n`.`group_sn` = {1} "
        ).format(gateway_sn, group_sn)

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


def update_app_group_node(gateway_sn: int, group_sn: int):
    try:
        sql = (
            "SELECT `a_n`.`node_sn` "
            "FROM `app_node` AS `a_n` "
            "INNER JOIN `app_group_node` AS `a_g_n` "
            "ON ( `a_n`.`gateway_sn` = `a_g_n`.`gateway_sn` "
            "AND `a_n`.`node_sn` = `a_g_n`.`node_sn` ) "
            "WHERE `a_g`.`gateway_sn` = {0} "
            "AND `a_g`.`group_sn` = {1} "
        ).format(gateway_sn, group_sn)

        dbh = MySQL()
        print(sql)
        results = dbh.execute(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


"""
app_scene:
"""


def select_app_scene(gateway_sn: int, scene_sn: int):
    try:
        sql = (
            "SELECT `a_s`.`scene_num` "
            "FROM `app_scene` AS `a_s` "
            "INNER JOIN `mqtt_gateway` AS `m_q` "
            "ON ( `a_s`.`gateway_sn` = `m_q`.`gateway_sn` ) "
            "WHERE `m_q`.`gateway_sn` = {0} "
            "AND `a_s`.`scene_sn` = {1} "
            "LIMIT 1 "
        ).format(gateway_sn, scene_sn)

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


"""
app_scene_node
"""


def select_app_scene_node(gateway_sn: int, scene_sn: int):
    try:
        sql = (
            "SELECT `a_n`.`node_sn`, `a_s_n`.`node_status`  "
            "FROM `app_node` AS `a_n` "
            "INNER JOIN `app_scene_node` AS `a_s_n` "
            "ON ( `a_n`.`gateway_sn` = `a_s_n`.`gateway_sn` "
            "AND `a_n`.`node_sn` = `a_s_n`.`node_sn` )"
            "WHERE `a_n`.`gateway_sn` = {0} "
            "AND `a_s_n`.`scene_sn` = {1} "
        ).format(gateway_sn, scene_sn)

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


"""
app_demand:
"""

def delete_app_demand(app_demand:AppDemand):
    try:
        sql = (
            
            ).format()
        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False
    
    
    
def update_app_demand(app_demand: AppDemand):
    try:
        sql = (
            "UPDATE `app_demand` "
            "SET `max_value` = {0}, `upper` = {1}, `lower` = {2}, "
            "`reload_gap` = {3}, `unload_mode` = {4}  "
            "WHERE `gateway_sn` = {5} "
        ).format(app_demand.max_value, app_demand.upper, app_demand.lower,
                 app_demand.reload_gap, app_demand.unload_mode,
                 app_demand.gateway_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False


"""
app_group
"""


def add_app_group(app_group: AppGroup):
    try:
        sql = (
            "INSERT INTO `app_group` "
            "(`gateway_sn`, `group_sn`, `area_sn`, `group_name`, `group_num`, `group_status`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}') "
        ).format(app_group.gateway_sn, app_group.group_sn, app_group.area_sn,
                 app_group.group_name, app_group.group_num, app_group.group_status)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False


def update_app_group(app_group: AppGroup):
    try:
        sql = (
            "UPDATE `app_group` "
            "SET `group_sn` = '{}' "
            "WHERE `gateway_sn` = '{}' AND `group_sn` = '{}' "
        ).format(app_group.group_sn,
                 app_group.gateway_sn, app_group.group_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False


def delete_app_group(app_group: AppGroup):
    try:
        sql = (
            "DELETE FROM `app_group` "
            "WHERE `gateway_sn` = '{}' AND `group_sn` = '{}' "
        ).format(app_group.gateway_sn, app_group.group_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False


"""
app_area:
"""


def add_app_area(app_area: AppArea):
    try:
        sql = (
            "INSERT INTO `app_area` "
            "(`gateway_sn`, `area_sn`, `area_name`) "
            "VALUES ('{0}', '{1}', '{2}') "
        ).format(app_area.gateway_sn, app_area.area_sn, app_area.area_name)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False


"""
app_user:
"""


def select_app_user():
    try:
        sql = (
            "SELECT * "
            "FROM `app_user` "
        )

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except BaseException as e:
        trace_error(e)
        return False


def select_app_user_by_user_id(user_id):
    try:
        sql = (
            "SELECT * "
            "FROM `app_user` "
            "WHERE `user_id` = '{0}' "
        ).format(user_id)

        dbh = MySQL()
        results = dbh.query(sql)
        dbh.close()

        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except BaseException as e:
        trace_error(e)
        return False


def insert_app_user(user_name: str, user_id: int):
    try:
        sql = (
            "INSERT INTO `app_user` "
            "(`user_name`, `user_id`) "
            "VALUES ('{0}', '{1}') "
        ).format(user_name, user_id)

        dbh = MySQL()
        result = dbh.execute(sql)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
        return False


"""
app_electricity:
"""


def insert_app_electricity(app_electricity: AppElectricity):
    try:
        sql = (
            "INSERT INTO `app_electricity` "
            "(`gateway_sn`,`electricity_sn`, `device_sn`, `demand_min`, `demand_quarter`, "
            " `R_value`, `S_value`, `T_value`, `total_value`, `recorded_time`, `created_time`) "
            "VALUES ('{0}', '{1}', '{2}', "
            " '{3}', '{4}', "
            " '{5}', '{6}', '{7}', '{8}', "
            " '{9}', '{10}') "
        ).format(app_electricity.gateway_sn, app_electricity.electricity_sn, app_electricity.device_sn,
                 app_electricity.demand_min, app_electricity.demand_quarter,
                 app_electricity.R_value, app_electricity.S_value, app_electricity.T_value, app_electricity.total_value,
                 app_electricity.recorded_time, app_electricity.created_time
                 )

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        print(result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except Exception as e:
        trace_error(e)
        return False
