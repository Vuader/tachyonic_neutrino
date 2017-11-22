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

from tachyonic.neutrino.validate import is_socket
from tachyonic.neutrino.threadlist import ThreadList

class Logger(object):
    class _Extra(logging.Filter):
        def __init__(self, get_extra):
            logging.Filter.__init__(self)
            self._get_extra = get_extra

        def filter(self, record):
            record.extra = self._get_extra()
            return True

    def set_extra(self, value):
        self._request.clear()
        self._request.append(value)

    def append_extra(self, value):
        self._request.append(value)

    def _get_extra(self):
        return " ".join(self._request)

    def __init__(self):
        self._request = ThreadList()
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)
        self.stdout = logging.StreamHandler()
        self.log.addHandler(self.stdout)
        log_format = logging.Formatter('%(asctime)s ' + '%(name)s[' +
                                       str(os.getpid()) +
                                       '] <%(levelname)s>: %(message)s', datefmt='%b %d %H:%M:%S')
        self.stdout.formatter = log_format

    def load(self, app_name='Neutrino', log_file=None, syslog_host='localhost',
             syslog_port=514, debug=False):

        if debug is True:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.WARNING)

        log_format = logging.Formatter('%(asctime)s ' + app_name + ' %(name)s[' + str(os.getpid()) +
                                       '] <%(levelname)s>: %(message)s %(extra)s', datefmt='%b %d %H:%M:%S')

        if syslog_host is not None:
            if syslog_host == '127.0.0.1' or syslog_host.lower() == 'localhost':
                if is_socket('/dev/log'):
                    syslog = logging.handlers.SysLogHandler(address='/dev/log')
                    self.log.addHandler(syslog)
                elif is_socket('/var/run/syslog'):
                    syslog = logging.handlers.SysLogHandler(address='/var/run/syslog')
                    self.log.addHandler(syslog)
                else:
                    syslog = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
                    self.log.addHandler(syslog)
            else:
                syslog = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
                self.log.addHandler(syslog)

        if log_file is not None:
            self.log.addHandler(logging.FileHandler(log_file))

        for handler in logging.root.handlers:
            handler.addFilter(self._Extra(self._get_extra))
            handler.formatter = log_format
