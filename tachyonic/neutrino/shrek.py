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
from queue import Queue

import pymysql as MySQLdb

from tachyonic.neutrino.threaddict import ThreadDict

log = logging.getLogger(__name__)

groups = {}

class Shrek(object):
    def __init__(self, group_name, call):
        self.group_name = group_name
        if group_name not in groups:
            groups[group_name] = {}
            groups[group_name]['thread'] = ThreadDict()

        self.group = groups[group_name]
        self._thread = groups[group_name]['thread']
        self.call = call

    def _pool(self, pool_name):
        if pool_name not in self.group:
            self.group[pool_name] = {}
            self.group[pool_name]['args'] = ()
            self.group[pool_name]['kwargs'] = {}

        if 'queue' not in self.group[pool_name]:
            self.group[pool_name]['queue'] = Queue(maxsize=0)

        return self.group[pool_name]

    def get(self, name, *args, **kwargs):
        pool = self._pool(name)

        if name in self._thread:
            log.debug("Using exisiting thread group %s pool %s (%s)" % (self.group_name,
                                                                        name,
                                                                        self._thread[name]))
            return self._thread[name]
        else:
            if len(args) > 0 and len(pool['args']) == 0:
                pool['args'] = args

            if len(kwargs) > 0 and len(pool['kwargs']) == 0:
                pool['kwargs'] = kwargs

            if pool['queue'].empty():
                r = self.call(*pool['args'], **pool['kwargs'])
                log.debug("New queue group %s pool %s (%s)" % (self.group_name,
                                                               name,
                                                               r))
                self._thread[name] = r
                return r
            else:
                r = pool['queue'].get(True)
                log.debug("Use queue group %s pool %s (%s)" % (self.group_name,
                                                               name,
                                                               r))
                self._thread[name] = r
                return r

    def put(self, name):
        pool = self._pool(name)
        if name in self._thread:
            log.debug("Return to queue group %s pool %s (%s)" % (self.group_name,
                                                                 name,
                                                                 self._thread[name]))
            if hasattr(self._thread[name], 'close'):
                self._thread[name].close()
            pool['queue'].put_nowait(self._thread[name])
            del self._thread[name]

    @staticmethod
    def close():
        for group in groups:
            for pool_name in groups[group]['thread']:
                q = groups[group][pool_name]['queue']
                obj = groups[group]['thread'][pool_name]
                if hasattr(obj, 'close'):
                    obj.close()
                q.put_nowait(obj)
                log.debug("Return to queue group %s pool %s (%s)" % (group,
                                                                     pool_name,
                                                                     obj))
            groups[group]['thread'].clear()
