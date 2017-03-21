from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import logging
import json
import traceback
import signal

from jinja2.exceptions import TemplateNotFound

import tachyonic as root
from tachyonic.neutrino.config import Config
from tachyonic.neutrino.redissy import redis
from tachyonic.neutrino.logger import Logger
from tachyonic.neutrino import restart
from tachyonic.neutrino.router import Router
from tachyonic.neutrino import template
from tachyonic.neutrino.utils.general import import_module
from tachyonic.neutrino.session import SessionFile
from tachyonic.neutrino.session import SessionRedis
from tachyonic.neutrino.headers import Headers
from tachyonic.neutrino.request import Request
from tachyonic.neutrino.response import Response
from tachyonic.neutrino.mysql import Mysql
from tachyonic.client.restclient import RestClient
from tachyonic.neutrino import constants as const
from tachyonic.neutrino import exceptions
from tachyonic.neutrino.web.dom import Dom
from tachyonic.neutrino.utils.general import if_unicode_to_utf8
from tachyonic.neutrino.policy import Policy


log = logging.getLogger(__name__)

root.router = Router()
root.jinja = template.Jinja()
root.render_template = root.jinja.render_template


class Wsgi(object):
    def __init__(self):
        self.running = False

    def __call__(self, app_root):
        try:
            self.running = True
            os.chdir(app_root)
            sys.path.append(app_root)
            self.router = root.router
            self.app_root = app_root.rstrip('/')
            config = "%s/settings.cfg" % (self.app_root,)
            policy = "%s/policy.json" % (self.app_root,)
            self.config = Config(config)
            self.app_config = self.config.get('application')
            self.log_config = self.config.get('logging')
            app_name = self.app_config.get('name','tachyonic')
            lfile = self.log_config.get('file', None)
            host = self.log_config.get('host')
            port = self.log_config.get('port', 514)
            debug = self.log_config.getboolean('debug')
            self.logger = Logger(app_name, host, port, debug, lfile)
            log.info("STARTING APPLICATION PROCESS FOR %s" % (app_name,))
            if debug is True:
                restart.start(interval=1.0)
                restart.track(config)
                restart.track(policy)

            self.context = {}
            self.app_config.getitems('modules')

            self.modules = self._modules()

            root.jinja.load_templates(self.config, app_root)
            middleware = self.app_config.getitems('middleware')
            self.middleware = self._m_objs(self.modules, middleware)

            if os.path.isfile(policy):
                policy = file(policy, 'r').read()
                self.policy = json.loads(policy)
            else:
                self.policy = None

            return self._interface

        except Exception as e:
            trace = str(traceback.format_exc())
            log.error("%s\n%s" % (e, trace))
            log.error("RESTARTING (pid=%d)" % os.getpid())
            try:
                self._cleanup()
            except:
                pass
            os.kill(os.getpid(), signal.SIGINT)
            return self._error_app

    def _error_template(self, req, code):
        for module in self.modules:
            try:
                t = root.jinja.get_template("%s.html" % (code))
                return t
            except TemplateNotFound:
                pass
            try:
                if req.is_ajax():
                    t = root.jinja.get_template("%s/%s_ajax.html" % (module, code))
                    return t
                else:
                    t = root.jinja.get_template("%s/%s.html" % (module, code))
                    return t

            except TemplateNotFound:
                pass

        return None

    def _error(self, e, req, resp):
        if hasattr(e, 'headers'):
            resp.headers.update(e.headers)

        if hasattr(e, 'status'):
            resp.status = e.status
        else:
            resp.status = const.HTTP_500

        if hasattr(e, 'code'):
            code = e.code
        else:
            code = resp.status.split(" ")[0]

        if hasattr(e, 'title'):
            title = e.title
        else:
            title = None

        if hasattr(e, 'description'):
            description = e.description
        else:
            description = repr(e)

        resp.clear()
        if resp.headers.get('Content-Type') == const.TEXT_PLAIN:
            if title is not None:
                resp.write("%s\n" % (title,))
            if description is not None:
                resp.write("%s" % (description,))
        elif resp.headers.get('Content-Type') == const.TEXT_HTML:
            t = self._error_template(req, code)
            if t is not None:
                resp.body = t.render(title=title, description=description)
            else:
                dom = Dom()
                html = dom.create_element('html')
                head = html.create_element('head')
                t = head.create_element('title')
                t.append(resp.status)
                body = html.create_element('body')
                if title is not None:
                    h1 = body.create_element('h1')
                    h1.append(title)
                if description is not None:
                    h2 = body.create_element('h2')
                    h2.append(description)
                resp.body = dom.get()
        elif resp.headers.get('Content-Type') == const.APPLICATION_JSON:
            j = {'error': {'title': title, 'description': description}}
            resp.body = json.dumps(j, indent=4)
        else:
            if title is not None:
                resp.write("%s\n" % (title,))
            if description is not None:
                resp.write("%s" % (description,))

        return resp

    def _cleanup(self):
        root.jinja.clean_up()
        RestClient().close_all()
        Mysql.close_all()
        self.logger.stdout.flush()
        sys.stdout.flush()
        sys.stderr.flush()

    def _error_app(self, environ, start_response):
        start_response('500 Internal Server Error'.encode('utf-8'), [])
        e = "{ \"error\": \"Tachyonic Neutrino Internal Application Error"
        e += " - Please view logs\" }"
        return [ str(e).encode('utf-8') ]

    # The application interface is a callable object
    def _interface(self, environ, start_response):
        # environ points to a dictionary containing CGI like environment
        # variables which is populated by the server for each
        # received request from the client
        # start_response is a callback function supplied by the server
        # which takes the HTTP status and headers as arguments

        # When the method is POST the variable will be sent
        # in the HTTP request body which is passed by the WSGI server
        # in the file like wsgi.input environment variable.
        try:
            debug = self.log_config.getboolean('debug')

            if 'redis' in self.config:
                rd = redis(self.config)
                session = SessionRedis(self.config, redis=rd)
            else:
                session = SessionFile(self.config, app_root=self.app_root)
            session_cookie = session.setup(environ)

            mysql_config = self.config.get('mysql')
            if mysql_config.get('database') is not None:
                Mysql(**mysql_config.dict())

            req = Request(environ, self.config, session, root.router, self.logger, self)
            resp = Response(req)

            resp.headers['Set-Cookie'] = session_cookie

            r = root.router.route(req)

            if debug is True:
                log.debug("Request URI: %s" % (req.get_full_path()))
                log.debug("Request QUERY: %s" % (req.environ['QUERY_STRING'],))

            response_headers = []
            static = self.config.get('application').get('static',
                                                        '').rstrip('/')
            root.jinja.globals['SITE'] = req.environ['SCRIPT_NAME']
            root.jinja.globals['STATIC'] = static
            root.jinja.request['REQUEST'] = req
            if root.jinja.globals['SITE'] == '/':
                root.jinja.globals['SITE'] = ''
            root.jinja.globals['STATIC'] = self.app_config.get('static',
                                                              '').rstrip('/')
            if root.jinja.globals['STATIC'] == '/':
                root.jinja.globals['STATIC'] = ''

            returned = None
            try:
                if r is not None:
                    route, obj_kwargs = r
                    method, route, obj, name = route
                    req.args = obj_kwargs
                    req.view = name
                else:
                    obj_kwargs = {}

                policy = Policy(self.policy, context=req.context, session=req.session, kwargs=obj_kwargs, qwargs=req.query)
                req.policy = policy

                for m in self.middleware:
                    if hasattr(m, 'pre'):
                        m.pre(req, resp)

                if r is not None:
                    if req.view is None or policy.validate(req.view):
                        returned = if_unicode_to_utf8(obj(req, resp, **obj_kwargs))
                    else:
                        raise exceptions.HTTPForbidden('Access Forbidden',
                                                       'Access denied by application' +
                                                       ' policy (%s)' % (req.view,))
                else:
                    raise exceptions.HTTPNotFound(description=req.environ['PATH_INFO'])

                for m in reversed(self.middleware):
                    if hasattr(m, 'post'):
                        m.post(req, resp)

            except exceptions.HTTPError as e:
                if debug is True:
                    trace = str(traceback.format_exc())
                    log.error("%s\n%s" % (e, trace))
                self._error(e, req, resp)
            except Exception as e:
                trace = str(traceback.format_exc())
                log.error("%s\n%s" % (e, trace))
                self._error(e, req, resp)

            resp.headers['X-Powered-By'] = 'Neutrino'
            resp.headers['X-Request-ID'] = req.request_id
            # HTTP headers expected by the client
            # They must be wrapped as a list of tupled pairs:
            # [(Header name, Header value)].
            for header in resp.headers:
                header = if_unicode_to_utf8(header)
                value = if_unicode_to_utf8(resp.headers[header])
                h = (header, value)
                response_headers.append(h)

            content_length = None

            if returned is None:
                content_length = resp.content_length
            else:
                if isinstance(returned, str):
                    content_length = len(returned)

            if content_length is not None:
                response_headers.append(('Content-Length'.encode('utf-8'),
                                         str(content_length).encode('utf-8')))

            # Send status and headers to the server using the supplied function
            start_response(resp.status, response_headers)

            self._cleanup()
            session.save()

            if returned is not None:
                return returned
            else:
                return resp
        except Exception as e:
            trace = str(traceback.format_exc())
            log.error("%s\n%s" % (e, trace))
            log.error("RESTARTING (pid=%d)" % os.getpid())
            try:
                self._cleanup()
            except:
                pass
            os.kill(os.getpid(), signal.SIGINT)

    def _modules(self):
        app_config = self.config.get('application')
        loaded = {}
        modules = app_config.getitems('modules')
        for module in modules:
            m = import_module(module)
            loaded[module] = m

        return loaded

    def _m_objs(self, modules, middleware):
        loaded = []
        for m in middleware:
            z = m.split('.')
            if len(z) > 1:
                l = len(z)
                mod = z[0:l-1]
                mod = '.'.join(mod)
                cls = z[l-1]
                mod = import_module(mod)
                if hasattr(mod, cls):
                    cls = getattr(mod, cls)
                    try:
                        loaded.append(cls())
                    except Exception as e:
                        trace = str(traceback.format_exc())
                        log.error("%s\n%s" % (str(e), trace))
                else:
                    raise ImportError(m)
            else:
                raise ImportError(m)
        return loaded

    def resources(self):
        def resource_wrapper(f):
            if self.running is True:
                f()

        return resource_wrapper

    def resource(self, method, resource, policy=None):
        def resource_wrapper(f):
            if self.running is True:
                return root.router.add(method, resource, f, policy)

        return resource_wrapper


app = Wsgi()
root.app = app
