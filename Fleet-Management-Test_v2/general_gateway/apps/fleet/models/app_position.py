from datetime import datetime
from app.utils.datetime_utils import iso8601_format_to_string


class AppPosition:
    def __init__(
            self,
            gateway_sn: int = 0,
            vehicle_id: int = 0,
            position_sn: int = 0,
            coordinate_x: float = 0.0,
            coordinate_y: float = 0.0,
            battery: float = 0.0,
            speed: float = 0.0,
            is_fault: int = 0.0,
            gateway_status: int = 0.0,
            timestamp: datetime = None
    ):
        self.gateway_sn = gateway_sn
        self.position_sn = position_sn
        self.vehicle_id = vehicle_id
        self.coordinate_x = coordinate_x
        self.coordinate_y = coordinate_y
        self.battery = battery
        self.speed = speed
        self.is_fault = is_fault
        self.gateway_status = gateway_status

        self.timestamp = iso8601_format_to_string(
            datetime.now().astimezone()) if timestamp is None else timestamp
