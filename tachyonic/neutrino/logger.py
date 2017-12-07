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

log_levels = [ 'CRITICAL'
               'ERROR',
               'WARNING',
               'INFO',
               'DEBUG' ]

class Logger(object):
    """Logger

    This class is the used to facilitate python logging facilities.
    """
    def __new__(cls):
        # Please keep singleton for future use. (christiaan.rademan@gmail.com)
        if not hasattr(cls, '_instance'):
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_init'):
            self._init = True
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
             syslog_port=514, level='WARNING'):
        """ Load / Configure Logging Facilities.

        Initially this method is used to configure logging facilities.

        Args:
            app_name (str): Application Name.
            log_file (str): Path to log file (default: None).
            syslog_host (str): IP or hostname of syslog server.
            syslog_port (int): Syslog Server Port (default: 514).
            log_level: Log output with set value and above as per order.
                * CRITICAL
                * ERROR
                * WARNING
                * INFO
                * DEBUG
        """

        level = level.upper()
        if level in log_levels:
            self.log.setLevel(getattr(logging, level))
        else:
            raise Exception('Invalid Logging Level %s' % level)

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

    class _Extra(logging.Filter):
        def __init__(self, get_extra):
            logging.Filter.__init__(self)
            self._get_extra = get_extra

        def filter(self, record):
            record.extra = self._get_extra()
            return True

    def _get_extra(self):
        return " ".join(self._request)

    def set_extra(self, value):
        """ Set Extra Logging Values.

        Set clears exisiting additional text to be appended to log messages and
        set adds new value.

        Args:
            value (str): Additional text to be appended to log message.
        """
        self._request.clear()
        self._request.append(value)

    def append_extra(self, value):
        """ Append Extra Logging Values.

        Append additional text to log messages.

        Args:
            value (str): Additional text to be appended to log message.
        """
        self._request.append(value)
