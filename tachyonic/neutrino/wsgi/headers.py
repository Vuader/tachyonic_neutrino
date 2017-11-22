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

import logging

log = logging.getLogger(__name__)


class Headers(object):
    def __init__(self, wsgi_environ=None):
        self._data = {}
        if wsgi_environ is not None:
            for p in wsgi_environ:
                p.replace('.', '-').lower()
                if len(p) > 5 and 'HTTP_' in p:
                    hk = p.replace('HTTP_', '')
                    self[hk] = wsgi_environ[p]

    def __setitem__(self, key, value):
        key = str(key).lower()
        key = key.replace('_','-')
        self._data[key] = value

    def __getitem__(self, key):
        key = str(key).lower()
        key = key.replace('_','-')
        if key in self._data:
            return self.get(key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        try:
            key = str(key).lower()
            key = key.replace('_','-')
            del self._data[key]
        except KeyError:
            pass

    def __contains__(self, key):
        key = str(key).lower()
        key = key.replace('_','-')
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return repr(self._data)

    def __str__(self):
        return str(self._data)

    def update(self, headers):
        for header in headers:
            ph = str(header).lower()
            ph = ph.replace('_','-')
            self._data[ph] = headers[header]

    def get(self, key, default=None):
        try:
            key = str(key).lower()
            key = key.replace('_','-')
            return str(self._data[key])
        except KeyError:
            return default
