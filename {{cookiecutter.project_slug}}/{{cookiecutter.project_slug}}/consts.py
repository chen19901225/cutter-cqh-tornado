
class ErrorCode(object):
    FIELD_MISSING = 100

    RECORD_NOT_FOUND = 200
    RECORD_EXISTS = 201

    REQUEST_RESULT_ERROR = 300
    REQUEST_ERROR = 301


msg_map = {
    ErrorCode.FIELD_MISSING: '字段缺失',
    ErrorCode.RECORD_NOT_FOUND: '记录未找到',
    ErrorCode.RECORD_EXISTS: '记录已存在',
    ErrorCode.REQUEST_ERROR: '请求错误',
    ErrorCode.REQUEST_RESULT_ERROR: '请求结果错误'
}


from {{cookiecutter.project_slug}}.settings import settings
from datetime import timezone, timedelta
default_datetime_format = settings['default_datetime_format']
default_zone_name = timezone(timedelta(hours=settings['zone_offset']))
