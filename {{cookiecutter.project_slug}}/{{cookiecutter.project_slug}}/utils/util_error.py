import json
import logging

logger = logging.getLogger(__name__)
from stackprinter import formatting
from {{cookiecutter.project_slug}}.settings import settings


def util_error_send_email(sender, task_id, exception, args, traceback, einfo, **kwargs):

    logger.info("[send_error_email]: {}, {}, {}".format(sender, task_id, exception))

    server_name = settings['server_name']

    lines = ['task_id:{}, args:{}, kwargs:{}\n'.format(task_id, args, kwargs)]

    exc_info = (type(exception), exception, traceback)
    lines.append(formatting.format_exc_info(*exc_info, truncate_vals=1000))
    content = ''.join(lines)

    # remote_email_helper = RemoteEmail.create_from_settings(email_settings_d)

    subject = 'error_notify:{}:celery:{}'.format(server_name, str(exception))

    logger.warning('send_error_email:{}'.format(content))
    from {{cookiecutter.project_slug}}.tasks.error.task_error_callback import error_callback
    error_callback.apply_async([json.dumps({
        'server_name': subject,
        'content': content
    })], queue='{{cookiecutter.project_slug}}_error')
