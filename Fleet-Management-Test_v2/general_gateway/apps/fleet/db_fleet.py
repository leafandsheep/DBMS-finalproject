import os
import json
import redis
from typing import Optional

from general_gateway.apps.fleet.models.enum.task_type import TaskType
from general_gateway.common.datetime_utils import ymdHMS_format_to_string
from general_gateway.common.db_utils import list_to_tuple_string
from general_gateway.common.mqtt_payload_util import transfer_payload_type
from general_gateway.common.trace_error_util import get_function_name, trace_error
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.models.general.mqtt_gateway import MQTTGateway
from general_gateway.models.general.mqtt_task import MQTTTask
from general_gateway.models.mysql import MySQL


def delete_mqtt_task_from_can_not_do_task_list(can_not_do_task_list: list, gateway_sn):
    try:
        delete_mqtt_task_tuple = list_to_tuple_string(can_not_do_task_list)

        sql = (
            "DELETE FROM `mqtt_task` "
            "WHERE `task_sn` IN {0} "
            "AND `gateway_sn` = '{1}' "
        ).format(delete_mqtt_task_tuple, gateway_sn)

        sql2 = (
            "DELETE FROM `app_task_information` "
            "WHERE `task_sn` IN {0} "
            "AND `gateway_sn` = '{1}' "
        ).format(delete_mqtt_task_tuple, gateway_sn)

        dbh = MySQL()
        print(sql)
        result = dbh.execute(sql)
        result = dbh.execute(sql2)
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

def select_mqtt_gateways(mac_address=None, gateway_status_list=None):
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

# FLEET_MANAGEMENT Database fetch
def insert_vehicle_coordinate(coordinate_x, coordinate_y, update_time):
    try:
        sql = (
            "INSERT INTO `app_vehicle_state` "
            "(`coordinate_x`, `coordinate_y`, `update_time`) "
            "VALUES ('{0}', '{1}', '{2}') "
        ).format(coordinate_x, coordinate_y, update_time)

        dbh = MySQL()
        print("insert_position: sql:", sql)
        result = dbh.execute(sql)
        print("insert_position: result:", result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
        return False

def select_latest_coordinate_without_timestamp():
    try:
        sql = (
            "SELECT `coordinate_x`, `coordinate_y` "
            "FROM `app_vehicle_state` "
            "ORDER BY `update_time` DESC LIMIT 1"
        )

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception("No position data found")

        return results
    except Exception as e:
        trace_error(e)
        return False

def select_latest_coordinate():
    try:
        sql = (
            "SELECT `coordinate_x`, `coordinate_y` , `update_time`"
            "FROM `app_vehicle_state` "
            "ORDER BY `update_time` DESC LIMIT 1"
        )

        dbh = MySQL()
        print(sql)
        results = dbh.query(sql)
        print(results)
        dbh.close()

        if not results:
            raise Exception("No position data found")

        return results
    except Exception as e:
        trace_error(e)
        return False

def get_coordinates_from_redis():
    redis_host = os.getenv('REDIS_HOST', 'iot_redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
    try:
        results = client.mget(['key1', 'key2'])
        if not results:
            raise Exception(get_function_name(), " Fail")

        return results
    except Exception as e:
        trace_error(e)
        return False


# 20231130：gateway status 插入 app_vehicle_state 的資料表
def insert_app_vehicle_state(gateway_sn, coordinate_x, coordinate_y, update_time):
    try:
        select_vehicle_id_sql = (
            "SELECT `vehicle_id` FROM  `app_vehicle`"
            "WHERE `gateway_sn`  = '{0}'"
        ).format(gateway_sn)

        dbh = MySQL()
        select_vehicle_id_result = dbh.query(select_vehicle_id_sql)
        dbh.close()

        for app_vehicle_id in select_vehicle_id_result:
            vehicle_id = app_vehicle_id.get('vehicle_id')


        select_gateway_status_sql = (
            "SELECT `gateway_status` FROM  `mqtt_gateway`"
            "WHERE `gateway_sn`  = '{0}'"
        ).format(gateway_sn)

        dbh = MySQL()
        select_gateway_status_result = dbh.query(select_gateway_status_sql)
        dbh.close()

        for app_gateway_status in select_gateway_status_result:
            gateway_status = app_gateway_status.get('gateway_status')

        sql = (
            "INSERT INTO `app_vehicle_state` "
            "(`vehicle_id`, `coordinate_x`, `coordinate_y`, `update_time`,`gateway_status`) "
            "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}') "
        ).format(vehicle_id, coordinate_x, coordinate_y, update_time, gateway_status)

        dbh = MySQL()
        # print("insert_position: sql:", sql)
        result = dbh.execute(sql)
        # print("insert_position: result:", result)
        dbh.close()

        if not result:
            raise Exception(get_function_name(), " Fail")

        return result
    except BaseException as e:
        trace_error(e)
        return False
    
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