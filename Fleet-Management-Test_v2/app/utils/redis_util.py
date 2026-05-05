
from typing import Optional

from app.utils.trace_error_util import trace_error
from config import REDIS

USER_TASK_HASH_NAME = "User_PickingList"
PREFIX_OF_TASK_ITEM_HASH_NAME = "PickingList_Item_"
LONG_DISTANCE_RFID_READER = "User_RFID2"

# def get_function_name():
#     return sys._getframe(1).f_code.co_name


def redis_reset():
    REDIS.flushdb()

def redis_delete_element(redis_key):
    try:
        result = REDIS.delete(redis_key)
        return result
    except Exception as e:
        trace_error(error=e)
        return False


def redis_delete_hash_element(hash_name, hash_key):
    try:
        result = REDIS.hdel(hash_name, hash_key)
        return result
    except Exception as e:
        trace_error(error=e)
        return False


def redis_get_user_task():
    redis_hash_name = "User_PickingList"
    result = REDIS.hgetall(redis_hash_name)
    if result:
        print(result)
    else:
        result = 0

    return result


def redis_get_hash_all(hash_name):
    result = REDIS.hgetall(hash_name)
    if result:
        print(result)
    else:
        result = 0

    return result


def redis_set_RFID_reader_statues(status):
    redis_key = "is_can_read_rfid"
    REDIS.set(redis_key, status)


def redis_get_RFID_reader_status():
    redis_key = "is_can_read_rfid"
    result = REDIS.get(redis_key)
    if result:
        result = int(result)
    else:
        result = 0

    return result


def redis_create_RFID_reader(rfid_reader):
    is_rfid_reader_exist = REDIS.exists(rfid_reader)
    if not is_rfid_reader_exist:
        redis_set_value_by_hash_name_and_id(rfid_reader, 'user1', 0)


def redis_get_scanned_RFID_tags(rfid_reader) -> Optional[list]:
    key_list = REDIS.hkeys(rfid_reader)
    rfid_tag_list = []

    for i in range(len(key_list)):
        rfid_tag_list.append((convert(key_list[i])))

    # if not rfid_tag_list:
    #     return None

    # if len(rfid_tag_list) == 1:
    #     rfid_tag_tuple = str(tuple(rfid_tag_list[:]))
    #     rfid_tag_tuple = rfid_tag_tuple.replace(",", "")
    # else:
    #     rfid_tag_tuple = str(tuple(rfid_tag_list[:]))

    return rfid_tag_list


def redis_get_scanned_RFID_tags_to_list(rfid_reader):
    key_list = REDIS.hkeys(rfid_reader)
    rfid_tag_list = []

    for i in range(len(key_list)):
        rfid_tag_list.append((convert(key_list[i])))

    if not rfid_tag_list:
        return None

    return rfid_tag_list


def redis_create_picking_list(task_sn, item_id, quantity):
    task_item_hash_name = PREFIX_OF_TASK_ITEM_HASH_NAME + str(task_sn)
    task_item_demand_hash_name = PREFIX_OF_TASK_ITEM_HASH_NAME + \
        str(task_sn) + "/Demand"

    # [使用者、單號]
    REDIS.hsetnx(USER_TASK_HASH_NAME, task_sn, 0)
    # [單號, 貨號, 所需數]
    redis_set_value_by_hash_name_and_id(
        task_item_demand_hash_name, item_id, quantity)
    # [單號, 貨號, 目前揀貨數]
    redis_set_value_by_hash_name_and_id(task_item_hash_name, item_id, 0)


def redis_get_tasks_num() -> Optional[int]:
    return REDIS.hlen(USER_TASK_HASH_NAME)


def redis_get_element_by_hash_name(hash_name=None) -> Optional[list]:
    if hash_name is None:
        return None
    key_list = REDIS.hkeys(hash_name)
    element_list = []

    if key_list is None:
        return None

    for key in key_list:
        element_list.append((convert(key)))

    if element_list:
        return element_list
    else:
        return None


def redis_get_value_by_hash_name_and_id(hash_name=None, hash_id=None):
    if hash_name is None or hash_id is None:
        return None

    return REDIS.hget(hash_name, hash_id)


def redis_set_value_by_hash_name_and_id(hash_name=None, hash_id=None, value=None):
    if hash_name is None or hash_id is None:
        return None
    REDIS.hset(hash_name, hash_id, value)


def convert(data):
    if isinstance(data, bytes):
        return data.decode('utf-8')
    if isinstance(data, dict):
        return dict(map(convert, data.items()))
    if isinstance(data, tuple):
        return map(convert, data)
    return data
