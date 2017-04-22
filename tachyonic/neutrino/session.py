# Copyright (c) 2016-2017, Christiaan Frans Rademan.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import logging
import pickle
import time
import datetime
import fcntl
import threading

from tachyonic.common.strings import if_unicode_to_utf8
from tachyonic.common.ids import random_id
from tachyonic.neutrino.redissy import redis

log = logging.getLogger(__name__)

lock = threading.Lock()


class SessionBase(object):
    def _cookie(self):
        name = if_unicode_to_utf8('tachyonic')
        self._expire = self.req.config.get('application').get('session_timeout')

        if name in self.req.cookies:
            session_id = self.req.cookies.get(name)
        else:
            session_id = if_unicode_to_utf8(random_id(16))
            self.req.cookies.set(name, session_id, self._expire)

        self._session_id = session_id
        self._load()


class SessionRedis(SessionBase):
    def __init__(self, request):
        self.req = request
        self._redis = redis()
        self._cookie()

    def _load(self):
        self._name = "session:%s" % (self._session_id,)
        if self._redis.hexists(self._name, 'session'):
            self._session = pickle.loads(self._redis.hget(self._name,
                                                         'session'))
        else:
            self._session = {}

    def save(self):
        if len(self._session) > 0:
            self._redis.expire(self._name, self._expire)
            self._redis.hset(self._name, 'session', pickle.dumps(self._session))

    def clear(self):
        self._session = {}
        try:
            self._redis.hdel(self._name, 'session')
        except:
            pass

    def __setitem__(self, key, value):
        self._session[key] = value

    def __getitem__(self, key):
        return self._session[key]

    def __delitem__(self, key):
        try:
            del self._session[key]
        except KeyError:
            pass

    def __contains__(self, key):
        return key in self._session

    def __iter__(self):
        return iter(self._session)

    def __len__(self):
        return len(self._session)

    def get(self, k, d=None):
        return self._session.get(k, d)


class SessionFile(SessionBase):
    def __init__(self, request):
        self.req = request
        self._path = "%s/tmp/" % (self.req.app_root,)
        self._cookie()

    def _load(self):
        lock.acquire()
        try:
            if os.path.isfile("%s%s.session" % (self._path, self._session_id,)):
                ts = int(time.mktime(datetime.datetime.now().timetuple()))
                stat = os.stat("%s%s.session" % (self._path, self._session_id))
                lm = int(stat.st_mtime)
                if ts - lm > self._expire:
                    self._session = {}

            if os.path.isfile("%s%s.session" % (self._path, self._session_id,)):
                h = open("%s%s.session" % (self._path, self._session_id,), 'rb', 0)
                fcntl.flock(h, fcntl.LOCK_EX)
                try:
                    self._session = pickle.load(h)
                finally:
                    fcntl.flock(h, fcntl.LOCK_UN)
                    h.close()
            else:
                self._session = {}
        finally:
            lock.release()

    def save(self):
        if len(self._session) > 0:
            lock.acquire()
            h = None
            try:
                h = open("%s%s.session" % (self._path, self._session_id,), 'wb', 0)
                fcntl.flock(h, fcntl.LOCK_EX)
                pickle.dump(self._session, h)
                h.flush()
                fcntl.flock(h, fcntl.LOCK_UN)
            finally:
                if h is not None:
                    h.close()
                lock.release()

    def clear(self):
        self._session = {}
        try:
            os.unlink("%s%s.session" % (self._path, self._session_id,))
        except:
            pass

    def __setitem__(self, key, value):
        self._session[key] = value

    def __getitem__(self, key):
        return self._session[key]

    def __delitem__(self, key):
        try:
            del self._session[key]
        except KeyError:
            pass

    def __contains__(self, key):
        return key in self._session

    def __iter__(self):
        return iter(self._session)

    def __len__(self):
        return len(self._session)

    def get(self, k, d=None):
        return self._session.get(k, d)
