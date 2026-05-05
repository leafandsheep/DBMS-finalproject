from datetime import datetime
from general_gateway.common.datetime_utils import iso8601_format_to_string
from general_gateway.models.enum.gateway_enum import GatewayStatus


class MQTTGateway:
    def __init__(
        self,
        gateway_sn: int = 0,
        gateway_mac_address: str = "",
        gateway_name: str = "",
        gateway_status: GatewayStatus = GatewayStatus.OFF,
        created_time: datetime = None,
        updated_time: datetime = None
    ):

        self.gateway_sn = gateway_sn
        self.gateway_mac_address = gateway_mac_address
        self.gateway_name = gateway_name
        self.gateway_status = gateway_status

        self.created_time = iso8601_format_to_string(
            datetime.now().astimezone()) if created_time is None else created_time

        self.updated_time = iso8601_format_to_string(
            datetime.now().astimezone()) if updated_time is None else updated_time
