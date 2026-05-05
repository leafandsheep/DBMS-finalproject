from enum import Enum


class TaskStatus(Enum):
    # 已制單
    CREATED = 0

    # 已派發
    DISPATCHED = 1

    # 執行中
    DOING = 2

    # 已成功
    SUCCEEDED = 3

    # 已中斷
    FAILED = 4

    # 已終止
    TERMINATED = 5
