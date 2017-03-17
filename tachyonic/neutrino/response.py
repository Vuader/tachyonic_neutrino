from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from tachyonic.neutrino import constants as const
from tachyonic.neutrino.headers import Headers
from tachyonic.neutrino.utils.general import if_unicode_to_utf8
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
        super(Response, self).__setattr__('headers', Headers(request=False))
        self.headers['Content-Type'] = const.TEXT_HTML
        super(Response, self).__setattr__('_io', StringIO())
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_req', req)
        self.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        self.headers['Progma'] = 'no-cache'
        self.headers['Expires'] = 0

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
