import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

key = "Q8lrMKUVVE"
from {{cookiecutter.project_slug}}.helper.helper_create import create_from_setting
from {{cookiecutter.project_slug}}.settings import settings

d = create_from_setting(settings)
from tornado import ioloop

loop = ioloop.IOLoop.current()

async def run():
    url_for_short = await d['service_sina'].generate_{{cookiecutter.project_slug}}("http://www.baidu.com")
    print("url_for_short:{}".format(url_for_short))

loop.run_sync(run)    







