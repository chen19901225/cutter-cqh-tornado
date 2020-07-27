import time
from {{cookiecutter.project_slug}} import consts
import datetime
import pytz


def util_time_current_timestamp():
    return int(time.time)


def util_time_now(zone_name):
    now = datetime.datetime.utcnow()
    return util_time_utc_to_local(now, zone_name)


utc = pytz.timezone("UTC")


def ensure_timezone(name_or_zone):
    if isinstance(name_or_zone, datetime.timezone):
        return name_or_zone
    return pytz.timezone(name_or_zone)


def util_time_datetime_str(v: datetime.datetime, fmt=consts.default_datetime_format,
                           zone_name=consts.default_zone_name):
    # 当remove_at为None,从数据库拿到的是这个
    if v == '0000-00-00 00:00:00':
        return '未设置'
    if not v:
        return '未设置'
    zone = ensure_timezone(zone_name)
    # out = v
    out = v.replace(tzinfo=utc).astimezone(tz=zone)

    return out.strftime(fmt)


def util_time_local_to_utc(v, zone_name=consts.default_zone_name):
    zone = ensure_timezone(zone_name)
    out = v.replace(tzinfo=zone).astimezone(tz=utc)

    return out


def util_time_utc_to_local(v, zone_name=consts.default_zone_name):
    zone_name = ensure_timezone(zone_name)
    out = v.replace(tzinfo=utc).astimezone(tz=zone_name)
    return out
