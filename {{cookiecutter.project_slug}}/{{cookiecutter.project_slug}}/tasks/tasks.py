
from celery import Celery
from celery.signals import task_failure
from celery.utils.log import get_task_logger
from {{cookiecutter.project_slug}}.settings import settings
logger = get_task_logger(__name__)
from tornado import httputil
# app = Celery('coder', broker_url='redis://localhost:6379/1')
# celery的redis不支持client_name
app = Celery('coder',
             broker=httputil.url_concat(settings['celery__broker_url'],
                                        dict(
             )
             ),
             backend=httputil.url_concat(settings['celery__broker_url'],
                                         dict(
             )
             ),
             include=['{{cookiecutter.project_slug}}.tasks.error.task_error_callback',
                      ])


# from coder.tasks.task_send_error_email import send_error_email
from {{cookiecutter.project_slug}}.utils.util_error import util_error_send_email

task_failure.connect()(util_error_send_email)
