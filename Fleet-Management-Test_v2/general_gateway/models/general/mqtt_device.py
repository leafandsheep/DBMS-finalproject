from datetime import datetime

from general_gateway.common.datetime_utils import iso8601_format_to_string


class MQTTDevice:
    def __init__(
        self,
        device_sn: int = 0,
        gateway_sn: int = 0,
        device_status: bool = False,
        device_meta: str = "",
        created_time: datetime = None,
        updated_time: datetime = None
    ):

        self.device_sn = device_sn
        self.gateway_sn = gateway_sn
        self.device_status = device_status
        self.device_meta = device_meta

        self.created_time = iso8601_format_to_string(
            datetime.now().astimezone()) if created_time is None else created_time

        self.updated_time = iso8601_format_to_string(
            datetime.now().astimezone()) if updated_time is None else updated_time
