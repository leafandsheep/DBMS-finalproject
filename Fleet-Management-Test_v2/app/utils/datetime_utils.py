import datetime as dt

from app.utils.datetime_enum import DateTimeType


def iso8601_format_to_string(date: dt.datetime) -> str:
    return date.strftime(DateTimeType.ISO8601_FORMAT.value)


def ymdHMS_format_to_string(date: dt.datetime) -> str:
    return date.strftime(DateTimeType.YMDHMS_FORMAT.value)


def string_convert_to_date(date_string: str, datetime_type: DateTimeType) -> dt.datetime:
    if date_string:
        return dt.datetime.strptime(date_string, datetime_type.value)
    else:
        return date_string


def datetime_format(date, from_datetime_type: DateTimeType, to_datetime_type: DateTimeType):
    return date.strftime(to_datetime_type.value)


def date_plus_hours(date: dt = dt.datetime.now(), hours: int = 0) -> dt.datetime:
    return date + dt.timedelta(hours=hours)


def date_minus_hours(date: dt = dt.datetime.now(), hours: int = 0) -> dt.datetime:
    return date - dt.timedelta(hours=hours)


def data_plus_seconds(date: dt = dt.datetime.now(), seconds: int = 0) -> dt.datetime:
    return date + dt.timedelta(seconds=seconds)
