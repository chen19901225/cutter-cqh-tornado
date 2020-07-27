import os
_dir = os.path.dirname(
    os.path.abspath(__file__)
)
proj_dir = _dir


settings = {
    'default_datetime_format': '%Y-%m-%d %H:%M:%S',
    'proj_dir': proj_dir,
    'zone_offset': 8,
    'day_format': "%Y-%m-%d",  # 日期格式，时间转成日期字符串
    'sina_{{cookiecutter.project_slug}}': "http://sina-t.cn/tcn/api",
    "burro_create_url": "https://www.admqr.com/apic/v1/api/cubes",
    "burro_update_url": "https://www.admqr.com/apic/v1/api/cubes/{id}/fast_modify",
    "sina_{{cookiecutter.project_slug}}_key": "Q8lrMKUVVE",
    "redis_url": "redis://127.0.0.1:6379/0",  # redis的url
    "celery__broker_url": "redis://127.0.0.1:6379/2",  # celery broker url
    "mattermost_url": "ttp://175.24.18.70:8065/hooks/jgc314eidbbgdfbbdmi7rtodyh"
}
