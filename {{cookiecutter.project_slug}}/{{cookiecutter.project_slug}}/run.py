import ipdb
from {{cookiecutter.project_slug}}.urls import url_pattern
import os
import tornado
from tornado import ioloop, log, escape, web
import signal
from tornado.options import define


def define_options():
    define('port', default=1080, help='listen port')
    define("debug", default=0, help="debug or not")
    define("name", default="{{cookiecutter.project_slug}}", help="确定进程的名字")


from {{cookiecutter.project_slug}} import utils
import datetime
from stackprinter import formatting
import logging


def error_callback(request_handler, exc_info):
    settings = request_handler.proj_settings
    server_name = settings['server_name'] + ':{}'.format(str(exc_info[1]))
    now = datetime.datetime.utcnow()
    out_lines = ['request_summary:{}\n'.format(request_handler._request_summary()),
                 'request:{}\n'.format(request_handler),
                 "now:{}\n".format(utils.util_time_datetime_str(now)),
                 "request_uri:{}\n".format(request_handler.request.uri),
                 "request_body:{}\n".format(request_handler.request.body),
                 "request_headers:{}\n".format(request_handler.request.headers),
                 ]
    if exc_info:
        out_lines.append("errors:{}\n".format(exc_info[0]))
        out_lines.append(formatting.format_exc_info(*exc_info, truncate_vals=1000))
        # for line in better_exceptions.format_exception(*exc_info):
        # out_lines.append(line)
    # generated_by_dict_unpack: request_handler
    logger = request_handler.logger
    if not logger.name.endswith(".error."):
        logger = logging.getLogger(logger.name + ".error.")
    logger.warning("error_callback:{}".format("send error msg"))
    # loop = ioloop.IOLoop.current()
    # func = http_email_send_from_settings(settings, server_name, ''.join(out_lines))
    logger.error('error_callback' + ''.join(out_lines))
    # service_manager: ServiceManager = request_handler.service_manager
    data = {
        'server_name': server_name,
        'content': ''.join(out_lines)
    }
    from {{cookiecutter.project_slug}}.tasks.tasks import task_web_send_web_error_email
    raw_str = escape.json_encode(data)
    task_web_send_web_error_email.apply_async([raw_str], queue='error')


def create_app(debug=False, **kwargs):
    log.gen_log.info("debug:{}".format(debug))
    log.gen_log.info("kwargs:{}".format(kwargs))
    log.gen_log.info("port:{}".format(kwargs['port']))
    log.gen_log.info("name:{}".format(kwargs['name']))

    template_path = os.path.join(kwargs['proj_dir'], 'templates')
    if not os.path.exists(template_path):
        raise Exception("template_path {} not exists".format(template_path))

    static_path = os.path.join(kwargs['proj_dir'], 'static')
    if not os.path.exists(static_path):
        raise Exception("static_path {} not exists" .format(static_path))

    import redis
    redis_client = redis.from_url(kwargs['redis_url'], client_name=kwargs['name'])
    workspace_root = os.path.dirname(kwargs['proj_dir'])
    doc_root = os.path.join(workspace_root, 'docs/_build/html')
    db_ip = ipdb.City(os.path.join(kwargs['proj_dir'], 'lib/lib_ip/ipipfree.ipdb'))

    app = web.Application(
        handlers=url_pattern,
        template_path=template_path,
        static_path=static_path,
        redis_client=redis_client,
        db_ip=db_ip,
        doc_root=doc_root,
    )
    return app


def sig_exit(signum, frame):
    log.gen_log.info("signum:{}".format(signum))
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(
        do_stop, signum=signum, frame=frame)


def do_stop(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()


def run_app(app, options):
    app.settings['options'] = options
    log.gen_log.info("port:{}".format(options.port))
    app.listen(options.port, xheaders=True)
    signal.signal(signal.SIGTERM, sig_exit)
    signal.signal(signal.SIGINT, sig_exit)

    loop: ioloop.IOLoop = ioloop.IOLoop.current()
    log.gen_log.info("start")
    loop.start()


if __name__ == "__main__":
    pass
