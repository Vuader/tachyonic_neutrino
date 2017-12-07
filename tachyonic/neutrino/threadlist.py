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

log = logging.getLogger(__name__)


class ThreadList(object):
    """Thread list.

    Allows thread safe and mutable iterations and unique sequence set of values
    per thread. Context for sequence of values being the thread id.

    Define globally for process and not within thread to take advantage of unique
    content functionality.
    """
    def __init__(self):
        self._threads = {}

    def _thread(self):
        self._thread_id = thread.get_ident()
        if self._thread_id not in self._threads:
            self._threads[self._thread_id] = []

        return self._threads[self._thread_id]

    def clear(self):
        """Clear sequence for thread.
        """
        self._thread_id = thread.get_ident()
        if self._thread_id in self._threads:
            del self._threads[self._thread_id]

    def append(self, value):
        """Appends object obj to list

        Args:
            Object/Value to be appended.
        """
        data = self._thread()
        data.append(value)

    def __setitem__(self, item, value):
        """Update value of item
        """
        data = self._thread()
        data[item] = value

    def __getitem__(self, item):
        """Get value of item.
        """
        data = self._thread()

        if item in data:
            return self.get(item)
        else:
            raise IndexError('list index out of range')

    def __delitem__(self, item):
        """Delete item in sequence.
        """
        data = self._thread()
        del data[item]

    def __contains__(self, item):
        """True if has a item, else False.
        """
        data = self._thread()

        return item in data

    def __iter__(self):
        """Return iterable of thread list.
        """
        data = self._thread()

        return iter(data)

    def __len__(self):
        """Return int length of thread list.
        """
        data = self._thread()

        return len(data)

    def __repr__(self):
        """Return representation of thread list.
        """
        data = self._thread()

        return repr(data)

    def __str__(self):
        """Return string of thread list.
        """
        data = self._thread()

        return str(data)
