import json
import random
import time
import threading
from datetime import datetime
import os

from flask import jsonify, Flask, request, Blueprint
from apscheduler.schedulers.background import BackgroundScheduler

# import General Gateway function
from ..models import *
from app.utils.trace_error_util import trace_error
from general_gateway.apps.fleet.db_fleet import select_latest_coordinate_without_timestamp, select_latest_coordinate
from general_gateway.common.datetime_utils import datetime_format
from general_gateway.models.enum.datetime_enum import DateTimeType
from general_gateway.apps.fleet.models.enum.task_type import TaskType
from general_gateway.common.db_utils import insert_mqtt_task, add_to_mqtt_message
from general_gateway.main import GeneralGateway
from general_gateway.models.enum.message_enum import MessageDirection, MessageType
from general_gateway.models.enum.project_name_enum import ProjectNameEnum
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.models.general.mqtt_task import MQTTTask
from setting import DB_CONFIG, BROKER_HOST, SERVER_ID, GATEWAY_ID, ROLE, GATEWAY_SN
from . import api

# 以通用閘道器模組替換原始啟動的程式碼
if not os.environ.get('GENERAL_GATEWAY_INITIALIZED'):
    general_gateway = GeneralGateway().set_db_connection(
        DB_CONFIG['host'],
        DB_CONFIG['user'],
        DB_CONFIG['password'],
        DB_CONFIG['db']
    ).set_basic_config( 
        BROKER_HOST,
        SERVER_ID,
        GATEWAY_ID,
        ROLE,
        ProjectNameEnum.FLEET_MANAGER
    ).set_custom_config(
        keys=['G_CONTROL_VALUE_TYPE_LIST'],
        values=[3]
    )
    # 確保只會生成一次General_Gateway
    general_gateway.start()
    os.environ['GENERAL_GATEWAY_INITIALIZED'] = '1'

generating = False

@api.route('/check_position', methods=['POST', 'GET'])
def check_position():
    try:
        mqtt_task = MQTTTask(
            gateway_sn=GATEWAY_SN,
            task_type=TaskType.GET_POSITION,
            task_status=TaskStatus.CREATED,
            content=json.dumps({})
        )
        mqtt_task.task_sn = insert_mqtt_task(mqtt_task)

        if not mqtt_task.task_sn:
            raise Exception("Insert mqtt_task " +
                            str(mqtt_task.task_sn) + " Fail.")
        if ROLE == "Gateway":
            direct = MessageDirection.FROM
        else:
            direct = MessageDirection.TO

        result = add_to_mqtt_message(
            is_need_ack=True,
            message_type=MessageType.REQUEST,
            mqtt_task=mqtt_task,
            direction=direct,
            gateway_id=GATEWAY_ID
        )
        if not result:
            raise Exception("Insert mqtt_message Fail.")

        return jsonify(result), 201
    except BaseException as e:
        trace_error(e)
        return "False", 400


# 替換成 Hybrid positioning framework
@api.route('/generate_position', methods=['POST', 'GET'])
def generate_position():
    global generating
    if generating:
        generating = False
        return jsonify({"message": "Stop Update"}), 200
    generating = True

    try:
        msg_generated = 0
        total_message = 1000
        while msg_generated < total_message:
            msg_generated += 1
            coordinate_x = round(random.uniform(0.00, 100.00), 2)
            coordinate_y = round(random.uniform(0.00, 100.00), 2)
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.')

            mqtt_task = MQTTTask(
                gateway_sn=GATEWAY_SN,
                task_type=TaskType.SEND_POSITION,
                task_status=TaskStatus.SUCCEEDED,
                content=json.dumps({
                    "coordinate_x": coordinate_x,
                    "coordinate_y": coordinate_y,
                    "update_time": timestamp
                })
            )

            # if ROLE == "Gateway":
            #     direct = MessageDirection.FROM
            # else:
            #     direct = MessageDirection.TO
            # 20240623 test priority msg
            # random_priority = random.randint(0, 5)
            result = add_to_mqtt_message(
                is_need_ack=True,
                message_type=MessageType.REQUEST,
                mqtt_task=mqtt_task,
                direction=MessageDirection.FROM,
                gateway_id=GATEWAY_ID
            )

            if not result:
                raise Exception("Insert mqtt_message Fail.")
            time.sleep(0.1)

            # time.sleep(0.2)
            # time.sleep(0.04)
            # time.sleep(0.025)
            # time.sleep(0.0181818)
            # time.sleep(0.0153846)
            # time.sleep(0.0142857)
            # time.sleep(0.0133333)
            # time.sleep(0.0125)
            # time.sleep(0.0117647)
            # time.sleep(0.0111111)
            # time.sleep(0.01)
            # time.sleep(0.0083333)
            
            # if msg_generated%10 == 0:
            #     time.sleep(1)

        # 成功執行完迴圈後，回傳成功訊息
        return jsonify({"message": "Position messages generated successfully"}), 200

    except BaseException as e:
        trace_error(e)
        return "False", 400

    
@api.route('get_latest_coordinates', methods = ['POST', 'GET'])
def get_latest_coordinates():
    try:
        data = select_latest_coordinate_without_timestamp()

        if data:
            coordinate_data = data[0]
            coordinate_x = coordinate_data['coordinate_x']
            coordinate_y = coordinate_data['coordinate_y']
            return jsonify({"coordinate-x": coordinate_x, "coordinate-y": coordinate_y})
        else:
            return jsonify({"error": "No coordinates available"}), 404
    except BaseException as e:
        trace_error(e)
        return "False", 400
