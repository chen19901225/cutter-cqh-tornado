from tornado import escape
from contextlib import contextmanager

import hashlib
import time


def util_common_md5(*args):
    h = hashlib.md5()
    for ele in args:
        h.update(escape.utf8(ele))
    return h.hexdigest()


def util_common_choices_to_map(choices):
    return {k: v for (k, v) in choices}


@contextmanager
def util_common_db_context(database):
    try:
        if database.is_closed():
            database.connect()
        yield database
    except OSError:
        print("We had an error!")
    finally:
        print("Closing db")
        if not database.is_closed():
            database.close()


@contextmanager
def util_common_loger_context(logger, prefix='test', method='info'):
    try:
        now = time.time()
        yield
    finally:
        end = time.time()
        getattr(logger, method)('{}: cost {}s'.format(prefix, (end - now)))
