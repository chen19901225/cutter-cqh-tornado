import datetime
from urllib import parse
from {{cookiecutter.project_slug}} import models
import copy
from {{cookiecutter.project_slug}} import exceptions
import peewee
import json
from {{cookiecutter.project_slug}} import consts, utils
from datetime import timedelta, timezone
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from tornado import web, log, escape, httputil, ioloop
import redis
import time


class TemplateRendring(object):
    """
    A simple class to hold methods for rendering templates.
    """

    def render_template(self, template_name, **kwargs):
        template_dirs = []
        if self.settings.get('template_path', ''):
            template_dirs.append(self.settings['template_path'])
        env = Environment(loader=FileSystemLoader(template_dirs))

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise TemplateNotFound(template_name)
        content = template.render(kwargs)
        return content


class HandlerBase(web.RequestHandler, TemplateRendring):
    # models = models

    @property
    def db(self):
        return self.settings['db']

    @property
    def logger(self):
        return self.settings['logger']

    @property
    def proj_settings(self):
        return self.settings['proj_settings']

    @property
    def errorcode(self) -> consts.ErrorCode:
        return self.settings['errorcode']

    @property
    def media_path(self):
        return self.settings['media_path']

    @property
    def default_datetime_format(self):
        return self.proj_settings['default_datetime_format']

    @property
    def default_zone_name(self):
        return timezone(timedelta(hours=self.proj_settings['zone_offset']))

    @property
    def redis_client(self) -> redis.Redis:
        return self.settings['redis_client']

    def native_str(self, param_str):
        return escape.native_str(param_str)

    def get_current_user(self):
        cookie_name = self.proj_settings['cookie_name']
        user_cookie_id = self.get_secure_cookie(cookie_name)
        if user_cookie_id is None:
            log.gen_log.info('get_current_user: user_cookie_id is None')
            return None
        # 这是未登录用户的token
        user_cookie_id = self.native_str(user_cookie_id)
        if user_cookie_id.startswith('nologin_'):
            return None
        user_cookie_record = self.service_manager.service_user.get_user_token_or_none(user_cookie_id)
        if user_cookie_record is None:
            log.gen_log.info('get_current_user: user_cookie_id {} cannot find record '.format(user_cookie_id))
            return None
        if user_cookie_record.is_expired():
            log.gen_log.info('get_current_user: user_cookie_id {} expires'.format(user_cookie_id))
            return None
        if user_cookie_record.is_locked:
            log.gen_log.info('get_current_user: user_cookie_id {} is locked'.format(user_cookie_id))
            return None

        user: models.MUser = self.service_manager.service_user.get_user_or_none_by_user_id(user_cookie_record.user_id)
        if user is None:
            log.gen_log.info('get_current_user: user_id {} not find user'.format(
                user_cookie_record.user_id
            ))
            return None
        if not user.is_active():
            log.gen_log.info('get_current_user: user_id {} is not active'.format(
                user_cookie_record.user_id
            ))
            return None
        if user.is_locked:
            log.gen_log.info('get_current_user: user_id {} is locked'.format(
                user_cookie_record.user_id
            ))
            return None
        if user.is_removed:
            log.gen_log.info("get_current_use: user_id:{} removed".format(
                user_cookie_record.user_id
            ))
            return None
        return user

    def cookie_page_size_get(self, default=20):
        value = self.get_cookie("_page_size")
        if value is None:
            return default
        return int(value)

    def render_html(self, template_name, **kwargs):
        # generated_by_dict_unpack: self
        current_user = self.current_user
        if current_user:
            user_url = self.service_manager.service_user.get_user_default_inframe_url(current_user,
                                                                                      self)
        else:
            user_url = None

        query_dict = dict(httputil.qs_to_qsl(self.request.query_arguments))
        query_dict = {k: escape.native_str(v) for (k, v) in query_dict.items()}
        query_json = escape.json_encode(query_dict)
        kwargs.update({
            'settings': self.settings,
            'STATIC_URL': self.settings.get('static_url_prefix', '/static/'),
            'request': self.request,
            'get_query_argument': self.get_query_argument,
            'get_query_arguments': self.get_query_arguments,
            'fetch_argument': self.fetch_argument,
            'static_url': self.static_url,
            'user_url': user_url,
            'consts': consts,
            'reverse_url': self.reverse_url,
            '_escape': 'escape',
            'query_json': query_json,
            'handler': self,
            'get_cookie': self.get_cookie,
            "cookie_show": self.get_cookie("_show"),
            'current_user': self.current_user,
            'title': '',
            'server_name': self.proj_settings['title'],
            'server_title': self.proj_settings['title'],
            'server_ip': self.proj_settings['server_ip'],
            'md5': utils.util_common_md5,
            'xsrf_token': self.xsrf_token,
            'xsrf_form_html': self.xsrf_form_html,
            '_menu_name': getattr(self, 'menu_name', self.get_default_menu_name()),
            'role_dict': {key: value for key, value in consts.user_role_desc_map.items() if key != consts.UserRole.DOWNSTREAM},
            '_item_name': getattr(self, 'item_name', self.get_default_item_name()),
            'time': time,
            'escape': escape,
            'day_range': self.day_range,
            'today_str': self.today().strftime("%Y-%m-%d"),
            'str': str,
            'cookie_page_size': self.cookie_page_size_get()
        })
        content = self.render_template(template_name, **kwargs)
        self.write(content)

    def day_range(self, start_day_str: str):
        date_format = self.proj_settings['day_format']
        start_day = datetime.datetime.strptime(start_day_str, date_format)
        end_day: datetime.datetime = start_day + datetime.timedelta(days=1)
        end_day_start = end_day.strftime(date_format)
        return '{} 00:00:00 | {} 00:00:00'.format(start_day_str, end_day_start)

    def prepare(self):
        # if self.db.is_closed():
        # 不管是不是closed,都connect
        with utils.util_common_loger_context(self.logger, 'prepare'):
            self.logger.info('db connect')
            self.redis_client.ping()
            if self.fetch_argument("_show"):
                self.request.cookies["_show"] = 1
                self.set_cookie("_show", value="1", expires_days=1)
            if not self.get_cookie("_page_size"):
                self.set_cookie("_page_size", "20")

            if self.db.is_closed():
                self.settings['db'].connect()
            for i in range(5):
                self.db.connection().ping(reconnect=True)
                # keep alive
                # models.MOptions.select().get()
                break

    @property
    def cmd_options(self):
        return self.settings['options']

    def get_listen_port(self):
        # 为了单元测试, 单元测试的时候没有options
        if 'options' in self.settings:
            return self.settings['options'].port
        else:
            return 1080
    # 不关闭了, 因为好像这个会导致多线程的时候 lose connection server during query这个bug的产生
    # 为什么开启的原因是因为，我不使用多线程了
    #

    def on_finish(self):
        if not self.db.is_closed():
            self.settings['db'].close()

    def on_connection_close(self):
        super().on_connection_close()
        # self.settings['db'].close()

    def try_self_error_callback(self, typ, value, tb):
        name = 'error_callback'
        if name in self.settings and self.settings[name]:
            # import logging
            # logging.info("try_self_error_callback:".format("callback"))
            self.settings[name](self, exc_info=(typ, value, tb))

    def log_exception(self, typ, value, tb):
        self.logger.error('log_exception before')
        try:
            self.try_self_error_callback(typ, value, tb)
        except Exception as e:
            self.logger.error("failt to call self_erro_callback %r" % e, exc_info=True)

        self.logger.error('log_exception after')
        return super().log_exception(typ, value, tb)

    def web_send_error(self, code, msg):
        self.set_status(400)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        d = {'code': code, 'msg': msg, 'data': None}
        convert_str = json.dumps(d, ensure_ascii=False)
        self.write(convert_str)

    def web_html_error(self, code, msg):
        self.set_status(400)
        self.write("{}".format(msg))
        #self.render_html("error.html", error_message=msg)

    def check_enable_machine_option_or_raise(self):
        option = self.enable_machine_options
        if option.value != "1":
            self.raise_error(
                self.errorcode.FIELD_VALUE_ERROR, "系统已关闭"
            )

    def web_send_data(self, data):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        d = {'code': 0, 'msg': '', 'data': data}
        self.write(json.dumps(d, ensure_ascii=False))

    def web_send_page_data(self, data, count, datetime_format=consts.china_full_datetime_format,
                           zone_name=consts.default_zone_name, extra=None):
        if data:
            if isinstance(data, peewee.ModelSelect):
                data = list(data)
            if not isinstance(data[0], dict):
                data = self.convert_list(data, datetime_format,
                                         zone_name=zone_name)
        self.write({'code': 0, 'msg': None, 'data': data, 'count': count,
                    'extra': extra})

    def raise_error(self, code, msg=None, detail=None):
        if msg is None:
            msg = consts.msg_map[code]
        raise exceptions.CustomErrorException(code=code, msg=msg,
                                              detail=detail)

    def send_error(self, status_code=500, **kwargs):
        from tornado import log
        log.gen_log.info('kwargs:{}'.format(kwargs))
        if 'exc_info' in kwargs and isinstance(kwargs['exc_info'][1], exceptions.CustomErrorException):
            exc = kwargs['exc_info'][1]
            self.web_send_error(exc.code, exc.msg)
            if not self._finished:
                self.finish()
            return

        return super().send_error(status_code=status_code, **kwargs)

    def convert_list(self, li, datetime_format=consts.china_full_datetime_format,
                     zone_name=consts.default_zone_name):
        out = []
        for ele in li:
            out.append(ele.to_json(datetime_format,
                                   zone_name=zone_name,
                                   request_handler=self))
        return out

    def arguments_unicode(self, arguments):
        obj = {}
        for key, values in arguments.items():
            values = [self.decode_argument(v) for v in values]
            obj[key] = values
        return obj

    @property
    def enable_machine_options(self) -> models.MOptions:
        option = models.MOptions._get_or_raise(
            [models.MOptions.name == consts.OptionName.ENABLE_MACHINE]
        )
        return option

    def get_or_create_prefetch_audit_count(self) -> models.MOptions:
        option = models.MOptions.get_or_none(
            name__eq="prefetch_audit_count"
        )
        if option is None:
            option = models.MOptions.create(
                name='prefetch_audit_count',
                value=str(0)
            )
        return option

    def can_create_order(self):
        # generated_by_dict_unpack: self
        enable_machine_options = self.enable_machine_options
        return enable_machine_options.value == "1"

    def fetch_argument(self, name, default=None, strip=True):
        return self.get_argument(name, default=default, strip=strip)

    def raise_missing_field(self, name):
        self.raise_error(
            self.errorcode.FIELD_MISSING, '字段{}缺失'.format(name)
        )

    def fetch_or_raise(self, name, expected_type=str):
        value = self.get_argument(name, None)
        if not value:
            self.raise_missing_field(name)
        if expected_type != str:
            try:
                return expected_type(value)
            except ValueError as e:
                self.logger.exception(e)
                self.raise_error(
                    self.errorcode.FIELD_VALUE_ERROR, "key{}类型错误{},".format(name, value)
                )

        return value

    def choices_to_map(self, choice_list):
        return {k: v for (k, v) in choice_list}

    def initialize(self, menu_name=None, item_name=None, title=None):
        self.menu_name = menu_name or self.get_default_menu_name()
        self.item_name = item_name or self.get_default_item_name()
        self.title = title or self.get_default_title()

    def get_default_menu_name(self):
        return ''

    def get_default_item_name(self):
        return ''

    def get_default_title(self):
        return ''

    def create_sequence_id(self) -> int:
        created_id = models.MNologinSerial.create_serial()
        return created_id

    def utf8(self, v):
        return escape.utf8(v)

    def get_login_cookie(self):
        return self.get_secure_cookie(self.proj_settings['cookie_name'])

    def today(self):
        now = datetime.datetime.utcnow()
        now = utils.util_time_utc_to_local(now)
        today = datetime.datetime(*now.timetuple()[:3])
        return today

    def today_utc(self):

        today = self.today()
        utc_today = utils.util_time_local_to_utc(today,
                                                 zone_name=consts.default_zone_name)
        return utc_today

    def set_default_headers(self):
        # self.set_header("Server", "thinkphp")
        self.clear_header("Server")

    def tomorrow(self):
        today = self.today()
        # begin = today - datetime.timedelta(days=30)
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow

    def get_default_time_range(self):
        today = self.today()
        tomorrow = self.tomorrow()
        range_list = [today, tomorrow]
        return self.generate_time_range(range_list)

    def generate_time_range(self, range_list):
        range_list = map(lambda x: x.strftime(
            consts.china_full_datetime_format), range_list)
        default_create_at = ' | '.join(range_list)
        return default_create_at

    def local_to_utc_for_list(self, li, zone_name):
        # return [utils.util_common_local_to_utc(e, zone_name) for e in li]
        return [utils.util_time_local_to_utc(e, zone_name) for e in li]

    def try_get_time_range(self, field_name, required=True, local_to_utc=True,
                           zone_name=consts.default_zone_name):
        value = self.fetch_argument(field_name)
        if not value and required:
            self.raise_missing_field(field_name)
        if " | " not in value:
            self.raise_error(
                self.errorcode.FIELD_VALUE_ERROR, "字段{}格式不对{}".format(field_name, value)
            )
        start_str, end_start = value.split(" | ", 1)
        try:
            start_str, end_start = map(lambda x: datetime.datetime.strptime(
                x, consts.china_full_datetime_format), [start_str, end_start])
            if local_to_utc:
                return self.local_to_utc_for_list([start_str, end_start], zone_name)
            else:
                return start_str, end_start

        except ValueError:
            self.raise_error(
                self.errorcode.FIELD_VALUE_ERROR, "字体{}格式不对{}".format(field_name, value)
            )

    def check_not_exist_or_raise(self, *keys):
        assert isinstance(keys, list)
        for key in keys:
            value = self.fetch_argument(key)
            if value:
                self.raise_error(
                    self.errorcode.FIELD_EXISTS, "字段{}不应该存在".format(key)
                )

    def get_can_edit_fields(self, fields, required=1, exclude_field_list = None):
        out_fields = []
        for e in fields:
            if e[2] == required:
                if exclude_field_list is None:
                    out_fields.append(e)
                else:
                    if e[0] not in exclude_field_list:
                        out_fields.append(e)
        return out_fields

    def run_in_executor(self, executor, func, *args):
        io_loop: ioloop.IOLoop = ioloop.IOLoop.current()

        def wrapper():
            # 原因
            # 这是因为pymysql的threadsafety级别为 1: Threads may share the module, but not connections.\
            # https://blog.51cto.com/kaifly/2358445
            # 但是想不明白为什么只有order_list这个页面有， 其他的order_list_export这些都没有，理由呢？
            # 难道是因为order_list这个有两个请求？
            # 这会产生连接数不停的增长
            self.db.connection().ping(reconnect=True)
            with self.db:
                return func(*args)
            # return func(*args)
        return io_loop.run_in_executor(executor, wrapper)

    def _log(self):
        if "log_function" in self.settings:
            self.settings["log_function"](self)
            return
        handler = self
        if handler.get_status() < 400:
            log_method = self.logger.info
        elif handler.get_status() < 500:
            log_method = self.logger.warning
        else:
            log_method = self.logger.error
        request_time = 1000.0 * self.request.request_time()
        log_method("%d %s %.2fms", handler.get_status(),
                   handler._request_summary(), request_time)

    # @property
    # def db_ip(self):
    #     if not hasattr(self, '_db_ip'):
    #         self._db_ip = ipdb.City(self.proj_settings['db_ip_path'])
    #     return self._db_ip

    def now(self):
        return utils.util_time_now(self.default_zone_name)
        # return util_common_now(self.default_zone_name)

    def get_argument_d(self):
        arguments = parse.parse_qs(escape.native_str(self.request.body), keep_blank_values=True)
        base_arguments = copy.deepcopy(self.request.query_arguments)

        for key, values in arguments.items():
            if values:
                base_arguments.setdefault(key, []).extend(values)

        # callbacks, type, total, api_order_sn, order_sn, sign = self.fetch_or_raise("callbacks"), self.fetch_or_raise("type"), self.fetch_or_raise("total"), self.fetch_or_raise("api_order_sn"), self.fetch_or_raise("order_sn"), self.fetch_or_raise("sign")
        d = dict(httputil.qs_to_qsl(base_arguments))
        d = {k: escape.native_str(v) for (k, v) in d.items() if v}
        return d
