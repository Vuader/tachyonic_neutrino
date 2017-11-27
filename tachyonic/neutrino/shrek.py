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
    """Pool Manager.

    A pool is a container for a collection of objects that are reuseable.

    Shrek will create pools based on groups of callables that return an object.
    As example it would typically be used for Mysql connection objects.

    Per process a unique group of pools are created for threads.

    A callable group example would be "connect" for "pymysql.connect". However in
    Neutrino there is a special wrapper that is given to provide a simple
    interface for pymysql. Groups can have prefixes when conflicted callable
    names are used.

    In each group multiple pools can be created based on name. Hence multiple
    mysql connections to different databases.

    Args:
        call: Callable function or class that returns object.
        prefix: Group of callable name prefix. (Optional)
            (good practice: __name__ of module)

    Shrek should be initilized globally within a module.
    """
    def __init__(self, call, prefix=None):
        if prefix is not None:
            self.group_name = "%s/%s" % (prefix, call.__name__)
        else:
            self.group_name = call.__name__
        if self.group_name not in groups:
            groups[self.group_name] = {}
            groups[self.group_name]['thread'] = ThreadDict()

        self.group = groups[self.group_name]
        self._thread = groups[self.group_name]['thread']
        self.call = call

    def _pool(self, pool_name):
        """Return pool for callable.

        If pool not found, it will be created.
        """
        if pool_name not in self.group:
            self.group[pool_name] = {}
            self.group[pool_name]['args'] = ()
            self.group[pool_name]['kwargs'] = {}

        if 'queue' not in self.group[pool_name]:
            self.group[pool_name]['queue'] = Queue(maxsize=0)

        return self.group[pool_name]

    def get(self, name, *args, **kwargs):
        """Get object from pool.

        If args and kwargs are provided they will be used to initilize the
        initial object.

        Args:
            name: Unique pool name for callable in group.

        Returns object from pool within group for thread.
        """
        pool = self._pool(name)

        if name in self._thread:
            log.debug("Using exisiting %s for thread in group %s pool %s"
                      % (self._thread[name],
                         self.group_name,
                         name))
            return self._thread[name]
        else:
            if len(args) > 0 and len(pool['args']) == 0:
                pool['args'] = args

            if len(kwargs) > 0 and len(pool['kwargs']) == 0:
                pool['kwargs'] = kwargs

            if pool['queue'].empty():
                r = self.call(*pool['args'], **pool['kwargs'])
                log.debug("New %s in group %s pool %s." % (r,
                                                           self.group_name,
                                                           name))
                self._thread[name] = r
                return r
            else:
                r = pool['queue'].get(True)
                log.debug("Using existing %s in group %s pool %s."
                          % (r,
                             self.group_name,
                             name))
                self._thread[name] = r
                return r

    def put(self, name):
        """Return object to pool.

        Args:
            name: Unique pool name for callable in group.
        """
        pool = self._pool(name)
        if name in self._thread:
            log.debug("Return %s to group %s pool %s."
                      % (self._thread[name],
                         self.group_name,
                         name))
            if hasattr(self._thread[name], 'close'):
                self._thread[name].close()
            pool['queue'].put_nowait(self._thread[name])
            del self._thread[name]

    @staticmethod
    def close():
        """Return all to pool.

        Returns all objects to pools for thread.
        """
        for group in groups:
            for pool_name in groups[group]['thread']:
                q = groups[group][pool_name]['queue']
                obj = groups[group]['thread'][pool_name]
                ### Not sure why close would be called here?
                ### Do not uncomment. christiaan.rademan@gmail.com
                #if hasattr(obj, 'close'):
                #    obj.close()
                q.put_nowait(obj)
                log.debug("Return object %s to group %s pool %s." % (obj,
                                                                     group,
                                                                     pool_name))
            groups[group]['thread'].clear()
