from app.api.mqtt_api.setting import ROLE
from app.api.mqtt_api.data.others.task_enum import TaskStatus, TaskType
from app.api.mqtt_api.data.others.item_enum import ItemStatus
from app.utils.database_util import select_mqtt_gateway_by_gateway_sn


def transform_task_status(task_status):
    if task_status == TaskStatus.CREATED:
        if ROLE == "Gateway":
            task_status = "待執行"
        elif ROLE == "Server":
            task_status = "待派發"
    elif task_status == TaskStatus.DISPATCHED:
        if ROLE == "Gateway":
            task_status = '待確認'
        elif ROLE == "Server":
            task_status = '已派發'
    elif task_status == TaskStatus.DOING:
        task_status = "執行中"
    elif task_status == TaskStatus.SUCCEEDED:
        task_status = '已成功'
    elif task_status == TaskStatus.FAILED:
        task_status = "異常"
    elif task_status == TaskStatus.TERMINATED:
        task_status = "已終止"

    return task_status

def transform_task_type(task_type):
    if task_type == TaskType.PICKUP:
        task_type = "揀貨"
    elif task_type == TaskType.INVENTORY:
        task_type = "盤點"

    return task_type


def transform_gateway_sn(gateway_sn):
    if gateway_sn:
        mqtt_gateway = select_mqtt_gateway_by_gateway_sn(gateway_sn)
        gateway_sn = mqtt_gateway.gateway_name
    else:
        gateway_sn = "無"

    return gateway_sn

def transform_item_status(item_status):
    if item_status == ItemStatus.EXCEPTION:
        item_status = "預設"
    elif item_status == ItemStatus.LOST:
        item_status = "遺失"
    elif item_status == ItemStatus.BROKEN:
        item_status = "損毀"
    elif item_status == ItemStatus.OTHERS:
        item_status = "其他"
    else:
        item_status = "其餘狀況"

    return item_status