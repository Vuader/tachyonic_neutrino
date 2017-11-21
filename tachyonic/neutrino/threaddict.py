# -*- coding: utf-8 -*-
# Copyright (c) 2017, Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import logging
import _thread as thread
import threading

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
