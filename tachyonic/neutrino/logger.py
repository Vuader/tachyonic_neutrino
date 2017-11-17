# -*- coding: utf-8 -*-
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

import logging
import logging.handlers
import os
import stat
try:
    import thread
except ImportError:
    import _thread as thread

from tachyonic.neutrino.validate import is_socket

class Logger(object):
    class _Extra(logging.Filter):
        def __init__(self, get_extra):
            logging.Filter.__init__(self)
            self._get_extra = get_extra

        def filter(self, record):
            record.extra = self._get_extra()
            return True

    def set_extra(self, value):
        thread_id = thread.get_ident()
        self._request[thread_id] = []
        self._request[thread_id].append(value)

    def append_extra(self, value):
        thread_id = thread.get_ident()
        if thread_id not in self._request:
            self._request[thread_id] = []
        self._request[thread_id].append(value)

    def _get_extra(self):
        thread_id = thread.get_ident()
        if thread_id in self._request:
            return " ".join(self._request[thread_id])
        else:
            return ""

    def __init__(self):
        self._request = {}
        self.log = logging.getLogger()
        self.log.setLevel(logging.INFO)
        self.stdout = logging.StreamHandler()
        self.log.addHandler(self.stdout)
        log_format = logging.Formatter('%(asctime)s ' + '%(name)s[' +
                                       str(os.getpid()) +
                                       '] <%(levelname)s>: %(message)s', datefmt='%b %d %H:%M:%S')
        self.stdout.formatter = log_format

    def load(self, app_name, config):
        log_config = config.get('logging')
        log_file = log_config.get('file', None)
        syslog_host = log_config.get('host', None)
        syslog_port = log_config.get('port', 514)
        debug = log_config.get_boolean('debug')

        if debug is True:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.WARNING)


        if syslog_host is not None:
            if syslog_host == '127.0.0.1' or syslog_host == 'localhost':
                if is_socket('/dev/log'):
                    syslog = logging.handlers.SysLogHandler(address='/dev/log')
                elif is_socket('/var/run/syslog'):
                    syslog = logging.handlers.SysLogHandler(address='/var/run/syslog')
                else:
                    syslog = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
            else:
                syslog = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))

        log_format = logging.Formatter('%(asctime)s ' + app_name + ' %(name)s[' + str(os.getpid()) +
                                       '] <%(levelname)s>: %(message)s %(extra)s', datefmt='%b %d %H:%M:%S')

        if syslog_host is not None:
            self.log.addHandler(syslog)

        if log_file is not None:
            self.log.addHandler(logging.FileHandler(log_file))

        for handler in logging.root.handlers:
            handler.addFilter(self._Extra(self._get_extra))
            handler.formatter = log_format
