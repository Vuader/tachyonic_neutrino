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

#threads = {}

lock = threading.Lock()

log = logging.getLogger(__name__)


class ThreadDict(object):
    def __init__(self):
        self.threads = {}

    def _thread(self):
        lock.acquire()
        try:
            self._thread_id = thread.get_ident()
            if self._thread_id not in self.threads:
                self.threads[self._thread_id] = {}
            return self.threads[self._thread_id]
        finally:
            lock.release()

    def clear(self):
        lock.acquire()
        try:
            self._thread_id = thread.get_ident()
            if self._thread_id in self.threads:
                del self.threads[self._thread_id]
        finally:
            lock.release()

    def __setitem__(self, key, value):
        data = self._thread()
        lock.acquire()
        try:
            data[key] = value
        finally:
            lock.release()

    def __getitem__(self, key):
        data = self._thread()
        if key in data:
            return self.get(key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        data = self._thread()
        lock.acquire()
        try:
            del data[key]
        finally:
            lock.release()

    def __contains__(self, key):
        data = self._thread()
        return key in data

    def __iter__(self):
        data = self._thread()
        return iter(data)

    def __len__(self):
        data = self._thread()
        return len(data)

    def __repr__(self):
        data = self._thread()
        return repr(data)

    def __str__(self):
        data = self._thread()
        return str(data)

    def update(self, update):
        data = self._thread()
        lock.acquire()
        try:
            data.update(update)
        finally:
            lock.release()

    def get(self, key, default=None):
        data = self._thread()
        return data.get(key, default)
