from datetime import datetime
from general_gateway.models.enum.message_enum import MessageType, MessageStatus


class MQTTMessage:
    def __init__(
        self,
        is_publish: bool = True,
        message_sn: int = 0,
        message_id: str = "",
        session_sn: int = 0,
        gateway_sn: int = 0,
        task_sn: int = 0,
        topic: str = "",
        payload: str = "",
        message_type: MessageType = MessageType.REQUEST,
        message_status: MessageStatus = MessageStatus.UNSENT,
        qos: int = 0,
        is_retain: bool = False,
        timestamp: datetime = None,
        is_need_ack=False
    ):
        self.message_sn = message_sn
        self.is_publish = is_publish
        self.message_id = message_id
        self.session_sn = session_sn
        self.gateway_sn = gateway_sn
        self.task_sn = task_sn
        self.topic = topic
        self.payload = payload
        self.message_type = message_type
        self.message_status = message_status
        self.qos = qos
        self.is_retain = is_retain
        self.timestamp = datetime.now().astimezone() if timestamp is None else timestamp
        self.is_need_ack = is_need_ack
