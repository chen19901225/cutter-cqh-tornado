from {{cookiecutter.project_slug}} import exceptions, consts
from tornado import escape
from urllib import parse
from {{cookiecutter.project_slug}}.settings import settings
from tornado.httpclient import AsyncHTTPClient
import logging

_logger = logging.getLogger(__name__)


class SSina(object):

    def __init__(self, key):
        self.key = key

    async def generate_{{cookiecutter.project_slug}}(self, url,
                                 logger=_logger) -> str:
        """
        反正一个url,如果失败就报错
        错误的情况:
           key不存在
           短网址余额不足，请充值后使用
        """
        _new_logger = logging.getLogger(logger.name + ".generate_{{cookiecutter.project_slug}}")
        _new_logger.info("url:{}".format(url))
        client = AsyncHTTPClient()
        base_url = settings['sina_{{cookiecutter.project_slug}}']
        data = {'key': self.key, 'url': url}
        final_url = base_url + '?' + parse.urlencode(data)
        _new_logger.info("final_url:{}".format(final_url))
        res = await client.fetch(final_url)
        body = escape.native_str(res.body)
        _new_logger.info("code:{}, body:{}".format(res.code, body))
        if body in ["短网址余额不足，请充值后使用", "key不存在"]:
            raise exceptions.CustomErrorException.from_httpclient_res(consts.ErrorCode.REQUEST_RESULT_ERROR, res)
        return body
