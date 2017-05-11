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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import datetime

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from tachyonic.common import exceptions
from tachyonic.common import constants as const
from tachyonic.common.headers import Headers
from tachyonic.common.strings import if_unicode_to_utf8
from tachyonic.common.dt import utc_time
from tachyonic.neutrino import router

log = logging.getLogger(__name__)


def http_moved_permanently(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_301
    resp.headers['Location'] = url


def http_found(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_302
    resp.headers['Location'] = url


def http_see_other(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_303
    resp.headers['Location'] = url


def http_temporary_redirect(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_307
    resp.headers['Location'] = url


def http_permanent_redirect(url, req, resp):
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_308
    resp.headers['Location'] = url


class Response(object):
    _attributes = ['status']

    def __init__(self, req=None):
        self.status = const.HTTP_200
        super(Response, self).__setattr__('headers', Headers())
        self.headers['Content-Type'] = const.TEXT_HTML
        super(Response, self).__setattr__('_io', StringIO())
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_req', req)

        # Default Headers
        self.headers['X-Powered-By'] = 'Tachyonic'
        self.headers['X-Request-ID'] = self._req.request_id

        # CACHING
        now = utc_time()
        now = datetime.datetime.strftime(now, "%a, %d %b %Y %H:%M:%S GMT")
        self.headers['Last-Modified'] = now

    def __setattr__(self, name, value):
        if name in self._attributes:
            super(Response, self).__setattr__(name, value)
        elif name == 'body':
            self.clear()
            super(Response, self).__setattr__('_io', StringIO())
            self.write(value)
        else:
            AttributeError("'response' object can't bind" +
                           " attribute '%s'" % (name,))

    def modified(self, datetime_obj):
        datetime_obj = datetime.datetime.strftime(datetime_obj, "%a, %d %b %Y %H:%M:%S GMT")
        self.headers['Last-Modified'] = str(datetime_obj)
        if datetime_obj == self._req.cached:
            raise exceptions.HTTPNotModified()


    def seek(self,position):
        self._io.seek(position)

    def read(self, size=0):
        if size == 0:
            return self._io.read()
        else:
            return self._io.read(size)

    def readline(self, size=0):
        if size == 0:
            return self._io.readline()
        else:
            return self._io.readline(size)

    def write(self, data):
        data = if_unicode_to_utf8(data)
        super(Response, self).__setattr__('content_length',
                                          len(data)+self.content_length)
        self._io.write(data)

    def clear(self):
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_io', StringIO())

    def __iter__(self):
        self._io.seek(0)
        return response_io_stream(self._io)

    def view(self, url, method):
        self.clear()
        router.view(url, method, self._req, self)

    def redirect(self, url):
        self.clear()
        http_see_other(url, self._req, self)


def response_io_stream(f, chunk_size=None):
    '''
    Generator to buffer chunks
    '''
    while True:
        if chunk_size is None:
            chunk = f.read()
        else:
            chunk = f.read(chunk_size)
        if not chunk:
            break
        yield if_unicode_to_utf8(chunk)
