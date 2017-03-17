from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging
if sys.version[0] == '2':
    import thread
else:
    import _thread as thread
import threading

threads = {}

lock = threading.Lock()

log = logging.getLogger(__name__)


class ThreadDict(object):
    def __init__(self):
        global threads
        lock.acquire()
        try:
            self._thread_id = thread.get_ident()
            if self._thread_id not in threads:
                threads[self._thread_id] = {}
            self.data = threads[self._thread_id]
        finally:
            lock.release()

    def __setitem__(self, key, value):
        lock.acquire()
        try:
            self.data[key] = value
        finally:
            lock.release()

    def __getitem__(self, key):
        if key in self.data:
            return self.get(key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        lock.acquire()
        try:
            del self.data[key]
        finally:
            lock.release()

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def update(self, update):
        lock.acquire()
        try:
            self.data.update(update)
        finally:
            lock.release()

    def get(self, key, default=None):
        return self.data.get(key, default)
