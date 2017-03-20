from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import logging.handlers
import os
import stat
try:
    import thread
except ImportError:
    import _thread as thread


class Logger(object):
    def _is_socket(self, socket):
        try:
            mode = os.stat(socket).st_mode
            is_socket = stat.S_ISSOCK(mode)
        except:
            is_socket = False
        return is_socket

    class _Filter(logging.Filter):
        def __init__(self, debug=False, get_extra=None):
            logging.Filter.__init__(self)
            self.debug = debug
            self._get_extra = get_extra

        def filter(self, record):
            if self._get_extra is not None:
                record.extra = self._get_extra()
            if record.levelno == logging.DEBUG:
                return self.debug
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

    def __init__(self, app_name, host, port, debug, lfile):
        self._request = {}

        logger = logging.getLogger()

        logger.setLevel(logging.DEBUG)


        if host is not None and (host == '127.0.0.1' or host == 'localhost'):
            if self._is_socket('/dev/log'):
                syslog = logging.handlers.SysLogHandler(address='/dev/log')
            elif self._is_socket('/var/run/syslog'):
                syslog = logging.handlers.SysLogHandler(address='/var/run/syslog')
            else:
                syslog = logging.handlers.SysLogHandler(address=(host, port))
        else:
            if host is not None:
                syslog = logging.handlers.SysLogHandler(address=(host, port))

        stdout = logging.StreamHandler()

        self.stdout = stdout

        log_format = logging.Formatter('%(asctime)s ' + app_name + ' %(name)s[' + str(os.getpid()) +
                                       '] <%(levelname)s>: %(message)s %(extra)s', datefmt='%b %d %H:%M:%S')

        if host is not None:
            syslog.formatter = log_format
            logger.addHandler(syslog)
        stdout.formatter = log_format
        logger.addHandler(stdout)
        if lfile is not None:
            fl = logging.FileHandler(lfile)
            fl.formatter = log_format
            logger.addHandler(fl)

        for handler in logging.root.handlers:
            handler.addFilter(self._Filter(debug=debug, get_extra=self._get_extra))
