from enum import Enum, IntEnum

class TaskType(Enum):
    NO_TASK = None
    SEND_POSITION = 1
    GET_POSITION = 2

class CMDStatus(Enum):
    # 已制單
    CREATED = 0

    # 執行中
    DOING = 1

    # 已成功
    SUCCEEDED = 2

    # 已中斷
    FAILED = 3

    # 已終止
    TERMINATED = 4

class CMDType(Enum):
    NO_CMD = None

    BATTERY = 1
    #傳送代步車電量訊息

    SPEED = 2
    #傳送代步車速度訊息

    AVOIDANCE = 3
    #傳送代步車避障訊息

    IS_FAULT = 4
    #傳送代步車故障碼訊息

    STOP = 5
    #傳送代步車剎車減速的請求

    ACCELERATE = 6
    #傳送代步車加速的請求

    TURN = 7
    #傳送代步車轉向的請求

    GET_POSITION = 8
    #傳送代步車定位座標

    SEND_POSITION = 9
    #定期發送座標

    FOLLOW = 10
    #傳送代步車跟隨的訊息

class CMDLayer(Enum):
    DATA = 'data_application_layer'
    ENV = 'environment_awareness_layer'
    V_CTL = 'vehicle_control_layer'