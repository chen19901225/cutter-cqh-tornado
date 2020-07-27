from {{cookiecutter.project_slug}} import utils
from {{cookiecutter.project_slug}}.tasks.tasks import app
from celery.utils.log import get_task_logger
from tornado import ioloop, escape
import functools
from {{cookiecutter.project_slug}}.settings import settings

logger = get_task_logger(__name__)


@app.task(name='task.error.callback')
def error_callback(raw_str):
    d = escape.json_decode(raw_str)
    # generated_by_dict_unpack: d
    server_name, content = d["server_name"], d["content"]
    logger.info("server_name:{}\ncontent:{}\n".format(
        server_name,
        content
    ))
    loop: ioloop.IOLoop = ioloop.IOLoop.current()
    logger.info("web_send_web_error_email started")
    loop.run_sync(functools.partial(utils.util_mattermost_send_text, settings['mattermost_url'], server_name, content, logger))
