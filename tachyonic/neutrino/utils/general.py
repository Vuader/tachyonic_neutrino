from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import string
import datetime
import random
import sys

def istext(s):
    # if s contains any null, it's not text:
    if "\0" in s:
        return False
    # an "empty" string is "text" (arbitrary but reasonable choice):
    if not s:
        return True
    return True


def import_module(module):
    __import__(module)
    return sys.modules[module]


class ObjectName(object):
    def _objectname(o):
        return o.__module__ + "." + o.__class__.__name__


def timer(started=None, pretty=False):
    if started is None:
        return datetime.datetime.now()
    else:
        seconds = (datetime.datetime.now()-started).total_seconds()
        if pretty is False:
            if seconds > 0.0001:
                return seconds
            else:
                return 0
        else:
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return "%d:%02d:%02d" % (h, m, s)


def random_id(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def if_unicode_to_utf8(string):
    if sys.version_info[0] == 2:
        if isinstance(string, unicode):
            return string.encode('utf-8')
        else:
            return string
    else:
        if isinstance(string, str):
            return string.encode('utf-8')
        else:
            return string


def is_byte_string(string):
    if sys.version_info[0] == 2:
        if isinstance(string, str):
            return True
        else:
            return False
    else:
        if isinstance(string, bytes):
            return True
        else:
            return False
