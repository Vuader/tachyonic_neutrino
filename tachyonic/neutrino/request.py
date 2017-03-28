from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import cgi
try:
    from urllib import parse as urlparse
    from urllib.parse import quote
except ImportError:
    import urlparse
    from urllib import quote

from tachyonic.neutrino.headers import Headers
from tachyonic.neutrino.utils.general import random_id

log = logging.getLogger(__name__)


class Request(object):
    def __init__(self, environ, config, session, router, logger, app):
        super(Request, self).__setattr__('context', {})
        super(Request, self).__setattr__('app_context', app.context)
        super(Request, self).__setattr__('config', config)
        super(Request, self).__setattr__('router', router)
        super(Request, self).__setattr__('logger', logger)
        super(Request, self).__setattr__('session', session)
        super(Request, self).__setattr__('environ', environ)
        super(Request, self).__setattr__('method', environ['REQUEST_METHOD'])
        super(Request, self).__setattr__('app', environ['SCRIPT_NAME'])
        super(Request, self).__setattr__('site', environ['SCRIPT_NAME'])
        super(Request, self).__setattr__('headers', Headers())
        super(Request, self).__setattr__('request_id', random_id(16))
        super(Request, self).__setattr__('view', None)

        self.logger.set_extra('(REQUEST:%s)' % self.request_id)
        self.logger.append_extra('(REMOTE_ADDR:%s)' % (self.environ['REMOTE_ADDR']))
        script_filename = self.environ.get('SCRIPT_FILENAME', 'None')
        self.logger.append_extra('(WSGI:%s)' % (script_filename,))

        for p in environ:
            p.replace('.', '_').lower()
            if len(p) > 5 and 'HTTP_' in p:
                hk = p.replace('HTTP_', '')
                self.headers[hk] = environ[p]
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

    def read(self, size=0):
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
        config = self.config
        app_config = config.get('application')
        use_x_forwarded_host = app_config.get('use_x_forwarded_host', False)
        if use_x_forwarded_host is True and 'X_FORWARDED_HOST' in self.headers:
            return self.headers['X_FORWARDED_HOST']
        elif 'SERVER_NAME' in self.environ:
            return self.environ['SERVER_NAME']
        elif 'SERVER_ADDR' in self.environ:
            return self.environ['SERVER_ADDR']
        else:
            return '127.0.0.1'

    def get_port(self):
        config = self.config
        app_config = config.get('application')
        use_x_forwarded_port = app_config.get('use_x_forwarded_port', False)
        if use_x_forwarded_port is True and 'X_FORWARDED_PORT' in self.headers:
            return self.headers['X_FORWARDED_PORT']
        elif 'SERVER_PORT' in self.environ:
            return self.environ['SERVER_PORT']

    def get_proto(self):
        return self.environ['wsgi.url_scheme']

    def get_script(self):
        if 'SCRIPT_NAME' in self.environ:
            return self.environ['SCRIPT_NAME']
        else:
            return None

    def get_app(self):
        return self.get_script()

    def get_path(self):
        url = quote(self.get_script())
        if 'PATH_INFO' in self.environ:
            url += quote(self.environ['PATH_INFO'])
        return url

    def get_full_path(self):
        url = self.get_path()
        if 'QUERY_STRING' in self.environ:
            url += '?' + self.environ['QUERY_STRING']

        return url

    def get_app_url(self):
        url = self.get_proto()+'://'
        url += self.get_host()

        if self.get_proto() == 'https':
            if self.get_port() != '443':
                url += ':' + self.get_port()
        elif self.get_proto() == 'http':
            if self.get_port() != '80':
                url += ':' + self.get_port()
                pass

        url += quote(self.get_script())
        return url

    def get_app_static(self):
        url = self.get_proto()+'://'
        url += self.get_host()

        if self.get_proto() == 'https':
            if self.get_port() != '443':
                url += ':' + self.get_port()
        elif self.get_proto() == 'http':
            if self.get_port() != '80':
                url += ':' + self.get_port()

        static = self.config.get("application").get("static", "/static")
        url += static

        return url

    def get_url(self):
        url = self.get_proto()+'://'
        url += self.get_host()

        if self.get_proto() == 'https':
            if self.get_port() != '443':
                url += ':' + self.get_port()
        elif self.get_proto() == 'http':
            if self.get_port() != '80':
                url += ':' + self.get_port()

        url += quote(self.get_script())
        if 'PATH_INFO' in self.environ:
            url += quote(self.environ['PATH_INFO'])

        return url

    def get_absolute_url(self):
        url = self.get_url()
        if 'QUERY_STRING' in self.environ:
            url += '?' + self.environ['QUERY_STRING']

        return url

    def is_secure(self):
        if self.get_proto() == 'https':
            return True
        else:
            return False

    def is_ajax(self):
        if ('X_REQUESTED_WITH' in self.headers and
                'xmlhttprequest' in self.headers['X_REQUESTED_WITH'].lower()):
            return True
        else:
            return False

    def is_mobile(self):
        # HTTP_USER_AGENT
        agent = self.headers.get('user_agent', '').lower()
        if 'iphone' in agent:
            return True
        elif 'android' in agent:
            return True
        else:
            return False

    def is_bot(self):
        # HTTP_USER_AGENT
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
    def __init__(self, fp, environ):
        self._cgi = cgi.FieldStorage(fp=fp, environ=environ)

    def _detected_post(self):
        """ DONT REMOVE USED FOR DETECTING OBJECT TYPE """
        pass

    def __getitem__(self, key):
        return self.get(key)

    def __contains__(self, key):
        try:
            return key in self._cgi
        except TypeError:
            return False

    def __iter__(self):
        return iter(self._cgi)

    def getfile(self, k):
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
