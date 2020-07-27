from {{cookiecutter.project_slug}} import consts
from tornado import escape


class CustomErrorException(Exception):
    def __init__(self, code, msg=None, detail=None):
        self.code = code
        self.msg = msg or consts.msg_map[code]
        self.detail = detail or ''
        super().__init__(code, msg)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__,
                                   self.code,
                                   self.msg,
                                   self.detail)
    __str__ = __repr__

    @classmethod
    def from_httpclient_res(cls, code, res, msg=None):
        info = 'request.url:{}, body:{}, res, code:{}, body:{}'.format(
            res.request.url,
            escape.native_str(res.request.body),
            res.code,
            escape.native_str(res.body)
        )
        msg = msg or info
        return cls(code, msg, info)
