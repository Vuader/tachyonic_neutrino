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
import cgi
from urllib import parse as urlparse
from urllib.parse import quote

from tachyonic.neutrino import js
from tachyonic.neutrino.exceptions import Error
from tachyonic.neutrino.wsgi.headers import Headers
from tachyonic.neutrino.wsgi.cookies import Cookies
from tachyonic.neutrino.ids import random_id
from tachyonic.neutrino.wsgi.session import SessionFile
from tachyonic.neutrino.wsgi.session import SessionRedis
from tachyonic.neutrino.rd import strict as redis

log = logging.getLogger(__name__)

class Request(object):
    """ WSGI Request

    Neutrino uses request and response objects to pass state through the
    system.

    When a page is requested: Neutrino creates an Request object that contains
    metadata about the request. The Request object represents the incoming HTTP
    request. It exposes properties and methods for examining headers, query
    string parameters, and other metadata associated with the request.
    Request is a file-like stream object for reading any data that was
    included in the body of the request. Neutrino loads the appropriate view,
    passing the Request as the first argument to the middleware and view function.

    The Request object also exposes a dict-like context property for passing
    arbitrary data to hooks and middleware methods. (request.context)

    Args:
        environ (dict): dictionary containing CGI like environment
            variables which is populated by the server for each received
            request from the client.
        app (object): neutrino wsgi object.

    Attributes:
        context (dict): per request context dictionary.
        app_context (dict): per process application context.
        config (object): Configuration, (neutrino.config.Config)
        router (object): Router. (neutrino.wsgi.router.Router)
        logger (object): Logging Facilitator. (neutrino.logger.Logger)
        environ (dict): dictionary containing CGI like environment
            variables which is populated by the server for each received
            request from the client.
        method (str): A  string representing the HTTP method used in the
            request. This is guaranteed to be uppercase.
        app (str): Application Entry Point.
            Same as mod_wsgi WSGIScriptAlias or example /ui.
        site (str): alias for app.
        headers (dict): A dictionary containing all available HTTP headers.
            Available headers depend on the client and server, but here are
            some examples.
            * CONTENT_LENGTH – The length of the request body (as a string).
            * CONTENT_TYPE – The MIME type of the request body.
            * HTTP_ACCEPT – Acceptable content types for the response.
            * HTTP_ACCEPT_ENCODING – Acceptable encodings for the response.
            * HTTP_ACCEPT_LANGUAGE – Acceptable languages for the response.
            * HTTP_HOST – The HTTP Host header sent by the client.
            * HTTP_REFERER – The referring page, if any.
            * HTTP_USER_AGENT – The client’s user-agent string.
            * QUERY_STRING – The query string, as a single (unparsed) string.
            * REMOTE_ADDR – The IP address of the client.
            * REMOTE_HOST – The hostname of the client.
            * REMOTE_USER – The user authenticated by the Web server, if any.
            * REQUEST_METHOD – A string such as "GET" or "POST".
            * SERVER_NAME – The hostname of the server.
            * SERVER_PORT – The port of the server (as a string).
            Any HTTP headers in the request are converted
            by settings all characters to uppercase, replacing any hyphens
            with underscores.
        cookies (object): A dictionary like object containing all cookies.
            Keys and values are strings.
        request_id (str): Unique Request ID.
        app_root (str): Application root file path.
        view (object): Current view method/function.
        session (object): A dictionary like object containing session data.
        content_length (int): The length of the request body in bytes.
        cached (str): Client Last-Modified header will contain the date of
            last modification. HTTP dates are always expressed in GMT,
            never in local time.
        query (object): A dictionary-like object containing all given HTTP
            QUERY parameters. (tachyonic.neutrino.wsgi.request.Get)
        post (object): A dictionary-like object containing all given HTTP POST
            parameters, providing that the request contains form data.
            (tachyonic.neutrino.wsgi.request.Post)
    """
    def __init__(self, environ, app):
        super(Request, self).__setattr__('context', {})
        super(Request, self).__setattr__('app_context', app.context)
        super(Request, self).__setattr__('config', app.config)
        super(Request, self).__setattr__('router', app.router)
        super(Request, self).__setattr__('logger', app.logger)
        super(Request, self).__setattr__('environ', environ)
        super(Request, self).__setattr__('method', environ['REQUEST_METHOD'])
        super(Request, self).__setattr__('app', environ['SCRIPT_NAME'])
        super(Request, self).__setattr__('site', environ['SCRIPT_NAME'])
        super(Request, self).__setattr__('headers', Headers(environ))
        super(Request, self).__setattr__('cookies', Cookies(self))
        super(Request, self).__setattr__('request_id', random_id(16))
        super(Request, self).__setattr__('app_root', app.app_root)
        super(Request, self).__setattr__('view', None)

        # Session Handling (req.session)
        if 'redis' in self.config and 'host' in self.config['redis']:
            session = SessionRedis(self)
        else:
            session = SessionFile(self)

        super(Request, self).__setattr__('session', session)

        self.logger.set_extra('(REQUEST:%s)' % self.request_id)
        self.logger.append_extra('(REMOTE_ADDR:%s)' % (self.environ['REMOTE_ADDR']))
        script_filename = self.environ.get('SCRIPT_FILENAME', 'None')
        self.logger.append_extra('(WSGI:%s)' % (script_filename,))

        try:
            super(Request, self).__setattr__('content_length',
                                             int(environ.get('CONTENT_LENGTH',
                                                 0)))
            self._input = environ['wsgi.input']
        except (ValueError):
            super(Request, self).__setattr__('content_length', 0)
            self._input = None

        self._read_field = False
        self._read_file = False
        self._post = None
        super(Request, self).__setattr__('query', Get(environ))

        # CACHING
        if 'If-Modified-Since' in self.headers:
            super(Request, self).__setattr__('cached',
                                             self.headers['If-Modified-Since'])
        else:
            super(Request, self).__setattr__('cached',
                                             None)

    def __setattr__(self, name, value):
        if name == 'method':
            super(Request, self).__setattr__(name, value.upper())
        elif name[0] == '_':
            super(Request, self).__setattr__(name, value)
        elif name == 'args' or name == 'view' or name == 'policy':
            super(Request, self).__setattr__(name, value)
        elif hasattr(self, name):
            raise AttributeError("'request' object can't rebind" +
                                 " attribute '%s'" % (name,))
        else:
            raise AttributeError("'request' object can't bind" +
                                 " attribute '%s'" % (name,))

    def __getattr__(self, name):
        name = name.lower()
        if name in self.__dict__:
            return self.__dict__[name]
        elif name == 'post':
            if self._post is None:
                if self._read_file is False:
                    self._post = Post(self._input, self.environ)
                else:
                    raise Exception("'You cannot use post after" +
                                    " reading from body'")
            self._read_field = True
            return self._post
        else:
            raise AttributeError("'request' object has no" +
                                 " attribute '%s'" % (name,))

    def json(self, size=0):
        """Return JSON Object from request body"""

        # JSON requires str not bytes hence decode.
        return js.loads(self.read())

    def read(self, size=0):
        """Read at most size bytes, returned as a bytes object.

        Returns content of response body.
        """
        if self._read_field is False:
            if self._input is not None:
                self._read_file = True
                if size == 0:
                    return self._input.read()
                else:
                    return self._input.read(size)
        else:
            raise Exception("'You cannot read from body after accessing post'")

    def readline(self, size=0):
        """Next line from the file, as a bytes object.

        Returns one line content of response body.
        """
        if self._read_field is False:
            if self._input is not None:
                self._read_file = True
                if size == 0:
                    return self._input.readline()
                else:
                    return self._input.readline(size)
        else:
            raise Exception("'You cannot read from body after accessing post'")

    def get_host(self):
        """ Returns the originating host.

        Uusing information from the HTTP_X_FORWARDED_HOST (if
        USE_X_FORWARDED_HOST is enabled) and HTTP_HOST headers, in that order.

        Example: "www.example.com"
        """
        config = self.config.get('application')
        use_x_forwarded_host = config.get('use_x_forwarded_host', False)

        if use_x_forwarded_host is True and 'X_FORWARDED_HOST' in self.headers:
            return self.headers['X_FORWARDED_HOST']
        elif 'SERVER_NAME' in self.environ:
            return self.environ['SERVER_NAME']
        elif 'SERVER_ADDR' in self.environ:
            return self.environ['SERVER_ADDR']
        else:
            raise Error('Server host not found')

    def get_port(self):
        """Returns the originating port.

        Using information from the HTTP_X_FORWARDED_PORT
        (if USE_X_FORWARDED_PORT is enabled) and SERVER_PORT META variables, in
        that order.
        """
        config = self.config
        app_config = config.get('application')
        use_x_forwarded_port = app_config.get('use_x_forwarded_port', False)
        if use_x_forwarded_port is True and 'X_FORWARDED_PORT' in self.headers:
            return self.headers['X_FORWARDED_PORT']
        elif 'SERVER_PORT' in self.environ:
            return self.environ['SERVER_PORT']
        else:
            raise Error('Server port not found')

    def get_proto(self):
        """Return the Protocol Scheme.

        A string representing the scheme of the request (http or https
        usually).
        """
        if 'wsgi.url_scheme' in self.environ:
            return self.environ['wsgi.url_scheme'].upper()
        else:
            raise Error('URI scheme not found')

    def get_script(self):
        """Return Application Entry point.

        For example:
            * WSGIScriptAlias as per mod_wsgi
            * /ui
        """
        if 'SCRIPT_NAME' in self.environ:
            return '/' + self.environ['SCRIPT_NAME'].strip('/')
        else:
            raise Error('Application entry point not found')


    def get_app(self):
        """Return Application Entry point.

        For example:
            * WSGIScriptAlias as per mod_wsgi
            * /ui
        """
        return self.get_script()

    def get_resource(self):
        """Returns the path exluding application entry point.

        Example: "/music/bands/metallica"
        """
        if 'PATH_INFO' in self.environ:
            url = quote(self.environ['PATH_INFO'])
            url = url.strip('/')
            if url != '':
                url = '/' + url
            return url
        else:
            raise Error('URL Resource path not found')

    def get_path(self):
        """Returns the path.

        Example: "/app/music/bands/metallica"
        """
        url = quote(self.get_script())
        if 'PATH_INFO' in self.environ:
            url += quote(self.environ['PATH_INFO'])
        return url


    def get_full_path(self):
        """Returns the path, plus an appended query string, if applicable.

        Example: "/app/music/bands/metallica?print=true"
        """
        url = self.get_path()
        if ('QUERY_STRING' in self.environ and
                self.environ['QUERY_STRING'] != ''):
            url += '?' + self.environ['QUERY_STRING']

        return url

    def get_app_url(self):
        """Returns the Appication URL form of location.

        Example: "https://example.com/app"
        """
        url = self.get_proto().lower()+'://'
        url += self.get_host()

        if self.get_proto() == 'HTTPS':
            if self.get_port() != '443':
                url += ':' + self.get_port()
        elif self.get_proto() == 'HTTP':
            if self.get_port() != '80':
                url += ':' + self.get_port()

        url += quote(self.get_script())
        return url

    def get_app_static(self):
        """Returns the static content path.

        Example: "/static"
        """
        static = self.config.get("application").get("static", "static")
        static = "/" + static.strip('/')

        return static

    def get_url(self):
        """Returns the URL form of location.

        Example: "https://example.com/app/music/bands/metallica"
        """
        url = self.get_app_url()
        url += quote(self.get_resource())

        return url

    def get_absolute_url(self):
        """Returns the absolute URL form of location.

        Example: "https://example.com/app/music/bands/metallica/?print=true"
        """
        url = self.get_app_url()
        url += quote(self.get_resource())
        if ('QUERY_STRING' in self.environ and
                self.environ['QUERY_STRING'] != ''):
            url += '?' + self.environ['QUERY_STRING']

        return url

    def is_secure(self):
        """Returns True if the request is secure.

        Tthat is, if it was made with HTTPS.
        """
        if self.get_proto() == 'HTTPS':
            return True
        else:
            return False

    def is_ajax(self):
        """Returns True if the request was made via an XMLHttpRequest.

        Checking the HTTP_X_REQUESTED_WITH header for the string
        'XMLHttpRequest'. Most modern JavaScript libraries send this header. If
        you write your own XMLHttpRequest call (on the browser side), you’ll
        have to set this header manually if you want is_ajax() to work.
        """
        if ('X_REQUESTED_WITH' in self.headers and
                'xmlhttprequest' in self.headers['X_REQUESTED_WITH'].lower()):
            return True
        else:
            return False

    def is_mobile(self):
        """Returns True if mobile client is used.

        Checking the HTTP_USER_AGENT header for known mobile strings.
        """
        agent = self.headers.get('user_agent', '').lower()
        if 'iphone' in agent:
            return True
        elif 'android' in agent:
            return True
        else:
            return False

    def is_bot(self):
        """Returns True if client is bot.

        Checking the HTTP_USER_AGENT header for known bot strings.
        """
        agent = self.headers.get('user_agent', '').lower()
        if 'google' in agent:
            return True
        elif 'bingbot' in agent:
            return True
        elif 'msnbot' in agent:
            return True
        elif 'adidxbot' in agent:
            return True
        elif 'bingpreview' in agent:
            return True
        elif 'yandex' in agent:
            return True
        elif 'yahoo' in agent:
            return True
        elif 'slurp' in agent:
            return True
        elif 'baidu' in agent:
            return True
        else:
            return False


class Post(object):
    """HTTP POST Data Object.

    Dictionary-like class customized to deal with multiple values for the
    same key. This is necessary because some HTML form elements, notably
    <select multiple>, pass multiple values for the same key.
    """
    def __init__(self, fp, environ):
        self.override = {}
        self._cgi = cgi.FieldStorage(fp=fp, environ=environ)

    def dict(self):
        """Returns Dict
        """
        dictionary = {}

        for field in self:
            dictionary[field] = self.get(field)

        return dictionary

    def json(self, debug):
        """Returns JSON
        """
        return js.dumps(self.dict(),
                        debug=debug)

    def __setitem__(self, key, value):
        self.override[key] = value

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        if key in self.override:
            return True
        try:
            return key in self._cgi
        except TypeError:
            return False

    def __iter__(self):
        return iter(self._cgi)

    def getfile(self, k):
        """Returns tuple with file data for the given key.

        Return Tuple:
            (str) File Name
            (str) Mime Type
            (bytes) Data
        """
        if k in self._cgi:
            f = self._cgi[k]
            name = f.filename
            if name == '':
                return None
            data = f.file.read()
            mtype = f.type
            return ( name, mtype, data )
        else:
            return None

    def get(self, k, d=None):
        """Returns the value for the given key.

        If the key has more than one value, it returns values comma
        seperated.
        """
        if k in self.override:
            return self.override[k]
        try:
            if k in self._cgi:
                val = ",".join(self._cgi.getlist(k))
                if val == '':
                    return None
                else:
                    return val
            else:
                return d
        except TypeError:
            return None

    def getlist(self, k, d=None):
        """Returns a list of the data with the requested key.

        Returns an empty list if the key doesn’t exist and a default value
        wasn’t provided. It’s guaranteed to return a list unless the default
        value provided isn’t a list.
        """
        try:
            if k in self._cgi:
                return self._cgi.getlist(k)
            else:
                if d is not None:
                    return d
                else:
                    return []
        except TypeError:
            return None


class Get(object):
    """URL Query Data Object.

    Dictionary-like class customized to deal with multiple values for the
    same key. This is necessary because some HTML form elements, notably
    <select multiple>, pass multiple values for the same key.
    """
    def __init__(self, environ):
        self._cgi = urlparse.parse_qs(environ['QUERY_STRING'])

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        try:
            return key in self._cgi
        except TypeError:
            return False

    def __iter__(self):
        return iter(self._cgi)

    def get(self, k, d=None):
        """Returns the value for the given key.

        If the key has more than one value, it returns values comma
        seperated.
        """
        try:
            if k in self._cgi:
                val = ",".join(self._cgi.get(k))
                if val == '':
                    return None
                else:
                    return val
            else:
                return d
        except TypeError:
            return None

    def getlist(self, k, d=None):
        """Returns a list of the data with the requested key.

        Returns an empty list if the key doesn’t exist and a default value
        wasn’t provided. It’s guaranteed to return a list unless the default
        value provided isn’t a list.
        """
        try:
            if k in self._cgi:
                return self._cgi.get(k)
            else:
                if d is not None:
                    return d
                else:
                    return []
        except TypeError:
            return None
