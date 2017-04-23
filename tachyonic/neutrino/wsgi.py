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
from __future__ import unicode_literals

import os
import sys
import logging
import json
import traceback
import signal

from jinja2.exceptions import TemplateNotFound

from tachyonic.neutrino import restart
from tachyonic.neutrino import template
from tachyonic.common import exceptions
from tachyonic.common import constants as const
from tachyonic.neutrino.config import Config
from tachyonic.neutrino.logger import Logger
from tachyonic.neutrino.router import Router
from tachyonic.neutrino.request import Request
from tachyonic.neutrino.response import Response
from tachyonic.neutrino.mysql import Mysql
from tachyonic.neutrino.redissy import redis
from tachyonic.neutrino.web.dom import Dom
from tachyonic.neutrino.policy import Policy
from tachyonic.neutrino.shrek import Shrek
from tachyonic.common.imports import import_module
from tachyonic.common.strings import if_unicode_to_utf8


log = logging.getLogger(__name__)


class Wsgi(object):
    """This class is the main entry point into a Neutrino app.

    Each API instance provides a callable WSGI interface.

    Attributes:
        app_root: Location of Application Root.
        router: Router Object used for adding routes.
        jinja: Jinja Interface Object. template.Jinja()
        get_template(template): Get Jinja Template shortcut.
            template.Jinja.get_template(template)
        render_template: Short cut Render Jinja Template.
            template.Jinja.render_template(template, \**kwargs)
        debug: Boolean if debug is enabled.
        logger: Logger Object - Tachyon Logging Facility Manager.
        context: Application Context - Per process
        policy: Policy Engine Object
        config: Configuration Object
    """

    def __init__(self):
        self.app_root = os.getcwd()
        self.router = Router()
        self.jinja = template.Jinja()
        self.get_template = self.jinja.get_template
        self.render_template = self.jinja.render_template
        self.debug = True
        self.context = {}
        self.policy = {}
        self.config = Config()
        self.logger = Logger()
        self._cleanup_funcs = []

    def __call__(self, app_root):
        """Initialize WSGI Application.

        Load settings.cfg, policies, logging and modules.

        Args:
            app_root (string): Root path for application where settings.cfg,
                overriding templates, static files and application tmp is located.

        Returns:
            method: (self.interface) method callable from WSGI server.
        """
        try:
            # Some default Attributes
            self.app_root = app_root.rstrip('/')

            # Ensure in application root
            os.chdir(self.app_root)

            # Prepend app_root to system path for python
            # imports during development
            sys.path.insert(0, self.app_root)

            # Load Configuration
            config_file_path = "%s/settings.cfg" % (self.app_root,)
            self.config.load(config_file_path)
            self.app_config = self.config.get('application')
            self.log_config = self.config.get('logging')
            self.debug = self.log_config.getboolean('debug')
            self.app_name = self.app_config.get('name','tachyonic')

            # Load Logger
            self.logger.load(self.app_name, self.config)
            log.info("STARTING APPLICATION PROCESS FOR %s" % (self.app_name,))

            # Load Policy if exisits
            policy_file_path = "%s/policy.json" % (self.app_root,)
            if os.path.isfile(policy_file_path):
                policy_file = file(policy_file_path, 'r')
                self.policy = json.loads(policy_file.read())
                policy_file.close()

            # Monitor Python modules and configs for changes.
            # If change detected kill myself... only while debug is enabled.
            # This makes it easier to do development...
            if self.debug is True:
                restart.start(interval=1.0)
                restart.track(config_file_path)
                restart.track(policy_file_path)

            # Load/Import modules
            self.app_config.getitems('modules')
            self.modules = self._modules()

            # Load Jinja Templates - Can only be performed after module import.
            # If done before you get poorly handled error messages.
            # Because jinja also trieds to import above moodules.
            self.jinja.load_templates(self.config, app_root)

            # Load Middleware - at this point modules should
            # already be imported.
            middleware = self.app_config.getitems('middleware')
            self.middleware = self._middleware(self.modules, middleware)

            # Return WSGI Callable Interface
            return self.interface

        except Exception as e:
            trace = str(traceback.format_exc())
            log.error("%s\n%s" % (e, trace))
            log.error("RESTARTING (pid=%d)" % os.getpid())

            try:
                self._cleanup()
            except:
                pass

            if self.debug is True:
                os.kill(os.getpid(), signal.SIGINT)

    def _error_template(self, req, code):
        # Scan for Custom Error templates.
        for module in self.modules:
            try:
                t = self.jinja.get_template("%s.html" % (code))
                return t
            except TemplateNotFound:
                pass
            try:
                if req.is_ajax():
                    t = self.jinja.get_template("%s/%s_ajax.html" % (module, code))
                    return t
                else:
                    t = self.jinja.get_template("%s/%s.html" % (module, code))
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

    def register_cleanup(self, function):
        """Register cleanup function run at end of request.

        Args:
            function (function): Any callable to run at end of request.
        """
        self._cleanup_funcs.append(function)

    def _cleanup(self):
        for func in self._cleanup_funcs:
            func()

        Shrek.close()
        self.jinja.clean_up()
        self.logger.stdout.flush()
        sys.stdout.flush()
        sys.stderr.flush()

    # The application interface is a callable object
    def interface(self, environ, start_response):
        """Interface callable for WSGI Server.

        May be used to host an API or called directly in order to simulate
        requests when testing API. See PEP3333.

        Args:
            environ (dict): dictionary containing CGI like environment
                variables which is populated by the server for each received
                request from the client.
            start_response (function): callback function supplied by the server
                which takes the HTTP status and headers as arguments.

        Returns:
            Iterable: Iterable containing none unicode - string or binary
            response body
        """
        try:
            # MYSQL Application Database
            mysql_config = self.config.get('mysql')
            if mysql_config.get('database') is not None:
                Mysql(**mysql_config.dict())

            # Redis
            redis_config = self.config.get('redis')
            if redis_config.get('host') is not None:
                redis(**redis_config.dict())

            # Request and Response Object
            req = Request(environ, self)
            resp = Response(req)

            # Debug Request logging
            if self.debug is True:
                log.debug("Request URI: %s" % (req.get_full_path()))
                log.debug("Request QUERY: %s" % (req.environ['QUERY_STRING'],))

            # Router to route based on Request
            r = self.router.route(req)

            # JINJA Globals
            static = self.config.get('application').get('static',
                                                        '').rstrip('/')
            self.jinja.globals['SITE'] = req.environ['SCRIPT_NAME']
            self.jinja.globals['STATIC'] = static
            self.jinja.request['REQUEST'] = req
            if self.jinja.globals['SITE'] == '/':
                self.jinja.globals['SITE'] = ''
            self.jinja.globals['STATIC'] = self.app_config.get('static',
                                                              '').rstrip('/')
            if self.jinja.globals['STATIC'] == '/':
                self.jinja.globals['STATIC'] = ''

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
                if self.debug is True:
                    trace = str(traceback.format_exc())
                    log.error("%s\n%s" % (e, trace))
                self._error(e, req, resp)
            except Exception as e:
                trace = str(traceback.format_exc())
                log.error("%s\n%s" % (e, trace))
                self._error(e, req, resp)

            # Content Length Header
            if returned is None:
                resp.headers['Content-Length'] = resp.content_length
            else:
                if isinstance(returned, str):
                    resp.headers['Content-Length'] = len(returned)

            # HTTP headers expected by the client
            # They must be wrapped as a list of tupled pairs:
            # [(Header name, Header value)].
            response_headers = []
            for header in resp.headers:
                header = if_unicode_to_utf8(header)
                value = if_unicode_to_utf8(resp.headers[header])
                h = (header, value)
                response_headers.append(h)

            # Set-Cookie Headers
            response_headers += req.cookies.headers()

            # Send status and headers to the server using the supplied function
            resp.status = if_unicode_to_utf8(resp.status)
            start_response(resp.status, response_headers)

            self._cleanup()
            req.session.save()

            if returned is None:
                return resp
            else:
                return returned

        except Exception as e:
            trace = str(traceback.format_exc())
            log.error("%s\n%s" % (e, trace))
            log.error("RESTARTING (pid=%d)" % os.getpid())

            try:
                self._cleanup()
            except:
                pass

            if self.debug is True:
                os.kill(os.getpid(), signal.SIGINT)

    def _modules(self):
        loaded = {}
        modules = self.app_config.getitems('modules')
        for module in modules:
            m = import_module(module)
            loaded[module] = m

        return loaded

    def _middleware(self, modules, middleware):
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
                    loaded.append(cls())
                else:
                    raise ImportError(m)
            else:
                raise ImportError(m)
        return loaded

    def resources(self):
        def resource_wrapper(f):
            f()

        return resource_wrapper

    def resource(self, method, resource, policy=None):
        def resource_wrapper(f):
            return self.router.add(method, resource, f, policy)

        return resource_wrapper
