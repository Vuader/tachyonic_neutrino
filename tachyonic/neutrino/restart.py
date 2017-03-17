from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import signal
import threading
import atexit
import logging
try:
    import queue as Queue
except ImportError:
    import Queue


_interval = 1.0
_times = {}
_files = []

_running = False
_queue = Queue.Queue()
_lock = threading.Lock()

log = logging.getLogger(__name__)


def _restart(path):
    _queue.put(True)
    prefix = 'RESTARTING (pid=%d):' % os.getpid()
    log.debug("%s Change detected to \'%s\'." % (prefix, path))
    log.debug("'%s Triggering process restart." % (prefix))
    os.kill(os.getpid(), signal.SIGINT)


def _modified(path):
    try:
        # If path doesn't denote a file and were previously
        # tracking it, then it has been removed or the file type
        # has changed so force a restart. If not previously
        # tracking the file then we can ignore it as probably
        # pseudo reference such as when file extracted from a
        # collection of modules contained in a zip file.

        if not os.path.isfile(path):
            return path in _times

        # Check for when file last modified.

        mtime = os.stat(path).st_mtime
        if path not in _times:
            _times[path] = mtime

        # Force restart when modification time has changed, even
        # if time now older, as that could indicate older file
        # has been restored.

        if mtime != _times[path]:
            return True
    except:
        # If any exception occured, likely that file has been
        # been removed just before stat(), so force a restart.

        return True

    return False


def _monitor():
    while 1:
        # Check modification times on all files in sys.modules.

        for module in sys.modules.values():
            if not hasattr(module, '__file__'):
                continue
            path = getattr(module, '__file__')
            if not path:
                continue
            if os.path.splitext(path)[1] in ['.pyc', '.pyo', '.pyd']:
                path = path[:-1]
            if _modified(path):
                return _restart(path)

        # Check modification times on files which have
        # specifically been registered for monitoring.

        for path in _files:
            if _modified(path):
                return _restart(path)

        # Go to sleep for specified interval.

        try:
            return _queue.get(timeout=_interval)
        except:
            pass


_thread = threading.Thread(target=_monitor)
_thread.setDaemon(True)


def _exiting():
    if _running:
        try:
            _queue.put(True)
        except:
            pass
        _thread.join()


atexit.register(_exiting)


def track(path):
    if path not in _files:
        _files.append(path)


def start(interval=1.0):
    global _interval
    if interval < _interval:
        _interval = interval

    global _running
    _lock.acquire()
    if not _running:
        log.debug("STARTING CHANGE MONITOR.")
        _running = True
        _thread.start()
    _lock.release()
