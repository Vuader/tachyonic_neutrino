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

status_codes = {100: 'Continue',
                101: 'Switching Protocols',
                200: 'OK',
                201: 'Created',
                202: 'Accepted',
                203: 'Non-Authoritative Information',
                204: 'No Content',
                205: 'Reset Content',
                206: 'Partial Content',
                226: 'IM Used',
                300: 'Multiple Choices',
                301: 'Moved Permanently',
                302: 'Found',
                303: 'See Other',
                304: 'Not Modified',
                305: 'Use Proxy',
                306: 'Switch Proxy',
                307: 'Temporary Redirect',
                308: 'Permanent Redirect',
                400: 'Bad Request',
                401: 'Unauthorized',
                402: 'Payment Required',
                403: 'Forbidden',
                404: 'Not Found',
                405: 'Method Not Allowed',
                406: 'Not Acceptable',
                407: 'Proxy Authentication Required',
                408: 'Request Time-out',
                409: 'Conflict',
                410: 'Gone',
                411: 'Length Required',
                412: 'Precondition Failed',
                413: 'Payload Too Large',
                414: 'URI Too Long',
                415: 'Unsupported Media Type',
                416: 'Range Not Satisfiable',
                417: 'Expectation Failed',
                418: "I'm a teapot",
                422: 'Unprocessable Entity',
                426: 'Upgrade Required',
                428: 'Precondition Required',
                429: 'Too Many Requests',
                431: 'Request Header Fields Too Large',
                451: 'Unavailable For Legal Reasons',
                500: 'Internal Server Error',
                501: 'Not Implemented',
                502: 'Bad Gateway',
                503: 'Service Unavailable',
                504: 'Gateway Time-out',
                505: 'HTTP Version not supported',
                511: 'Network Authentication Required'}

class Headers(object):
    """ WSGI Headers.

    Behaves like a dictionary storing HTTP headers.

    Args:
        wsgi_environ: Loads WSGI Environment headers.
    """
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

    def wsgi_headers(self):
        """Return headers for WSGI

        HTTP headers expected by the client
        They must be wrapped as a list of tupled pairs:
            [(Header name, Header value)].
        """

        headers = []

        for header in self:
            value = self[header]
            h = (header, value)
            headers.append(h)

        return headers
