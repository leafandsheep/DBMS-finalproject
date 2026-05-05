from enum import Enum


class DateTimeType(Enum):
    YMDHMS_FORMAT = "%Y-%m-%d %H:%M:%S"
    ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
