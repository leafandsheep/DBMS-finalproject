import configparser
import json
import uuid
from datetime import datetime
from typing import Optional

from general_gateway.common.datetime_utils import iso8601_format_to_string, string_convert_to_date
from general_gateway.common.mqtt_payload_util import transfer_payload_type
from general_gateway.common.trace_error_util import trace_error
from general_gateway.models.enum.config_enum import ConfigEnum
from general_gateway.models.enum.datetime_enum import DateTimeType
from general_gateway.models.enum.message_enum import MessageType
from general_gateway.models.enum.project_name_enum import ProjectNameEnum
from general_gateway.models.enum.task_enum import TaskStatus
from general_gateway.models.general.mqtt_message import MQTTMessage
from general_gateway.models.general.mqtt_task import MQTTTask


def read_task_payload(topic, payload):
    try:
        server_id, direct, gateway_mac = topic.split('/')
        payload = transfer_payload_type(payload, to_type=dict)

        from general_gateway.apps.fleet.db_fleet import select_mqtt_gateways
        gateway_sn = select_mqtt_gateways(gateway_mac)[0].gateway_sn

        if not gateway_sn:
            raise Exception("read_payload(): no gateway_sn")

        mqtt_task = MQTTTask(
            task_sn=payload.get('header').get('task_sn'),
            gateway_sn=gateway_sn,
            task_id=payload.get('header').get('task_id'),
            task_type=payload.get('header').get('task_type'),
            task_timeout=payload.get('header').get('task_timeout'),
            task_priority=payload.get('header').get('task_priority'),
            task_status=TaskStatus(payload.get('header').get('task_status')),
            content=transfer_payload_type(payload.get('content'), to_type=str),
            created_time=string_convert_to_date(
                payload.get('header').get('task_created_time'),
                DateTimeType.ISO8601_FORMAT
            ),
            updated_time=string_convert_to_date(
                payload.get('header').get('task_updated_time'),
                DateTimeType.ISO8601_FORMAT
            )
        )

        return mqtt_task
    except BaseException as e:
        trace_error(e)
        return None


def write_task_payload(
        message_id="",
        message_type: MessageType = MessageType.REQUEST,
        is_need_ack=True,
        mqtt_task: MQTTTask = None
):
    try:
        header = {
            'message_id': str(uuid.uuid4()) if message_id == "" else message_id,
            'message_type': message_type.value,
            'message_timestamp': iso8601_format_to_string(datetime.now().astimezone()),
            'is_need_ack': is_need_ack
        }

        if mqtt_task is not None:
            header['task_sn'] = mqtt_task.task_sn
            header['task_id'] = mqtt_task.task_id
            header['task_type'] = mqtt_task.task_type.value
            header['task_timeout'] = mqtt_task.task_timeout
            header['task_priority'] = mqtt_task.task_priority
            header['task_status'] = mqtt_task.task_status.value
            if type(mqtt_task.created_time) == str:
                header['task_created_time'] = mqtt_task.created_time
            elif type(mqtt_task.created_time) == datetime:
                header['task_created_time'] = iso8601_format_to_string(mqtt_task.created_time)
            if type(mqtt_task.updated_time) == str:
                header['task_updated_time'] = mqtt_task.created_time
            elif type(mqtt_task.updated_time) == datetime:
                header['task_updated_time'] = iso8601_format_to_string(mqtt_task.updated_time)

            if mqtt_task.content:
                if type(mqtt_task.content) == str:
                    content = json.loads(mqtt_task.content)
                else:
                    content = mqtt_task.content
            else:
                content = {}
        else:
            content = {}

        payload = {}
        payload.setdefault('header', header)

        if payload.get('content'):
            payload['content'] = content
        else:
            payload.setdefault('content', content)

        return payload
    except BaseException as e:
        trace_error(e)


def read_ack_payload(payload):
    try:
        payload = transfer_payload_type(payload, to_type=dict)
        print("read_ack_payload: payload.get('header').get('task_sn'):", payload.get('header').get('task_sn'))
        print("read_ack_payload: type(payload.get('header').get('task_sn')):",
              type(payload.get('header').get('task_sn')))
        return payload.get('header').get('gateway_sn'), payload.get('header').get('task_sn', [])
    except BaseException as e:
        trace_error(e)


def write_request_can_do_payload(
        message_type,
        is_need_ack: bool = False,
        message_id: str = "",
        task_sn_list: list = [],
        can_do_mqtt_tasks: list = [],
        can_not_do_mqtt_tasks: list = [],
) -> Optional[dict]:
    try:
        header = {
            'message_id': str(uuid.uuid4()) if message_id == "" else message_id,
            'message_type': message_type.value,
            'message_timestamp': iso8601_format_to_string(datetime.now().astimezone()),
            'is_need_ack': is_need_ack,
        }
        content = {}

        if task_sn_list:
            content.update({'request_can_do_task_sn': task_sn_list})
        if can_do_mqtt_tasks:
            content.update({'can_do_task_sn': can_do_mqtt_tasks})
        if can_not_do_mqtt_tasks:
            content.update({'can_not_do_task_sn': can_not_do_mqtt_tasks})

        payload = {
            'header': header,
            'content': content
        }

        return payload
    except BaseException as e:
        trace_error(e)


def read_request_can_do_task_content(mqtt_message: MQTTMessage):
    try:
        request_can_do_task_list = None
        can_do_task_list = None
        can_not_do_task_list = None

        content = mqtt_message.message_payload.get('content')

        if content:
            request_can_do_task_list = content.get('request_can_do_task_sn')
            can_do_task_list = content.get('can_do_task_sn')
            can_not_do_task_list = content.get('can_not_do_task_sn')

        return request_can_do_task_list, can_do_task_list, can_not_do_task_list

    except BaseException as e:
        trace_error(e)


# FIXME: 2022/10/26 app model
def read_task_content(mqtt_task: MQTTTask):
    try:
        app_items = mqtt_task.content.get('app_items_on_the_list')
        app_inventory_records = mqtt_task.content.get('app_inventory_record')
        mqtt_tasks = mqtt_task.content.get('request_can_do_task_sn')

        if app_items:
            for app_item in app_items:
                item = AppItem(
                    task_sn=mqtt_task.task_sn,
                    gateway_sn=mqtt_task.gateway_sn,
                    item_id=app_item.get('item_id'),
                    item_sn=app_item.get('item_sn'),
                    item_name=app_item.get('item_name'),
                    item_status=app_item.get('item_status'),
                    quantity=app_item.get('quantity')
                )
                app_item_rfids = app_item.get('app_item_rfid')
                if app_item_rfids:
                    for app_item_rfid in app_item_rfids:
                        item_rfid = AppItemRFID(
                            rfid=app_item_rfid.get('rfid'),
                            created_time=app_item_rfid.get('created_time'),
                            rfid_status=app_item_rfid.get('rfid_status'),
                            rfid_location=app_item_rfid.get('rfid_location')
                        )
                        item.app_item_rfids.append(item_rfid)
                mqtt_task.app_items.append(item)

        if app_inventory_records:
            for inventory_rfid, record_time in app_inventory_records.items():
                app_item_rfid = AppItemRFID(
                    rfid=inventory_rfid,
                    last_inventory_time=record_time
                )
                mqtt_task.app_inventory_records.append(app_item_rfid)

        if mqtt_tasks:
            for task_sn in mqtt_tasks:
                mqtt_task.mqtt_tasks.append(task_sn)

        return mqtt_task
    except BaseException as e:
        trace_error(e)

# def write_pickup_content(mqtt_task: MQTTTask, is_response=0):
#     try:
#         if is_response:
#
#             if mqtt_task.task_status == TaskStatus.FAILED:
#                 items = []
#                 content = {
#                     'app_items_on_the_list': [],
#                 }
#                 for item in mqtt_task.app_items:
#                     items.append({
#                         'item_id': item.item_id,
#                         'item_sn': item.item_sn,
#                         'item_status': item.item_status,
#                     })
#                     content['app_items_on_the_list'] = items
#             else:
#                 content = {}
#         else:
#             items = []
#
#             content = {
#                 'app_items_on_the_list': [],
#             }
#
#             for item in mqtt_task.app_items:
#                 items.append({
#                     'item_id': item.item_id,
#                     'quantity': item.quantity,
#                 })
#                 content['app_items_on_the_list'] = items
#         return content
#     except BaseException as e:
#         trace_error(e)
#
#
# def write_inventory_content(mqtt_task: MQTTTask = None, is_response=0):
#     try:
#         if not is_response:
#             content = {}
#         else:
#             content = {}
#             inventory_records = {}
#
#             if mqtt_task:
#                 from app.utils.database_util import select_app_item_rfid_by_created_time_and_last_inventory_time
#                 results = select_app_item_rfid_by_created_time_and_last_inventory_time(mqtt_task)
#
#                 if results:
#                     for result in results:
#                         inventory_records.update({result.get('rfid'):str(result.get('last_inventory_time'))})
#                 content['app_inventory_record'] = inventory_records
#
#         return content
#     except BaseException as e:
#         trace_error(e)
