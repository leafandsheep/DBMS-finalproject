import datetime as dt
from general_gateway.models.enum.datetime_enum import DateTimeType


def iso8601_format_to_string(date: dt.datetime) -> str:
    return date.strftime(DateTimeType.ISO8601_FORMAT.value)


def ymdHMS_format_to_string(date: dt.datetime) -> str:
    return date.strftime(DateTimeType.YMDHMS_FORMAT.value)


def string_convert_to_date(date_string: str, datetime_type: DateTimeType) -> dt.datetime:
    if date_string:
        return dt.datetime.strptime(date_string, datetime_type.value)
    else:
        return date_string

# 20240125 調整紀錄時間到毫秒等級
# def datetime_format(date, from_datetime_type: DateTimeType, to_datetime_type: DateTimeType):
#     return date.strftime(to_datetime_type.value)

def datetime_format(date, from_datetime_type: DateTimeType, to_datetime_type: DateTimeType):
    if isinstance(date, str):
        date_obj = dt.strptime(date, from_datetime_type.value)
    else:
        date_obj = date
    
    formatted_date = date_obj.strftime(to_datetime_type.value)

    if to_datetime_type == DateTimeType.ISO8601_FORMAT:
        return formatted_date[:-3]
    else:
        return formatted_date

def date_plus_hours(date: dt = dt.datetime.now(), hours: int = 0) -> dt.datetime:
    return date + dt.timedelta(hours=hours)


def date_minus_hours(date: dt = dt.datetime.now(), hours: int = 0) -> dt.datetime:
    return date - dt.timedelta(hours=hours)


def data_plus_seconds(date: dt = dt.datetime.now(), seconds: int = 0) -> dt.datetime:
    return date + dt.timedelta(seconds=seconds)
