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

import os
import sys
import logging
import json
import traceback
import signal

from jinja2.exceptions import TemplateNotFound

from tachyonic.neutrino import exceptions
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.imports import import_module, get_class
from tachyonic.neutrino.strings import if_unicode_to_utf8
from tachyonic.neutrino.dt import Datetime
from tachyonic.neutrino import restart
from tachyonic.neutrino import template
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
from tachyonic.neutrino.wsgi.base import Base
from tachyonic.neutrino.wsgi.error import Error

log = logging.getLogger(__name__)


class Wsgi(Base, Error):
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

            # Datetime Object and exposement
            dt = Datetime()
            req.context['datetime'] = dt
            self.jinja.globals['DATETIME'] = dt

            try:
                if r is not None:
                    obj, methods, obj_kwargs, route, name = r
                    req.args = obj_kwargs
                    req.view = name
                else:
                    obj_kwargs = {}

                policy = Policy(self.policy, context=req.context, session=req.session, kwargs=obj_kwargs, qwargs=req.query)
                req.policy = policy

                for m in self.middleware:
                    if hasattr(m, 'pre'):
                        m.pre(req, resp)

                returned = None
                if r is not None:
                    if req.view is None or policy.validate(req.view):
                        returned = obj(req, resp, **obj_kwargs)
                        if isinstance(returned, (str, bytes)):
                            resp.write(returned)
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
                    log.debug("%s\n%s" % (e, trace))
                self._error(e, req, resp)
            except Exception as e:
                trace = str(traceback.format_exc())
                log.error("%s\n%s" % (e, trace))
                self._error(e, req, resp)

            # Content Length Header
            resp.headers['Content-Length'] = str(resp.content_length)

            # Send status and headers to the server using the supplied function
            start_response(resp.status, resp.wsgi_headers())

            # Clean Process
            self._cleanup()

            # Save Client Session
            req.session.save()

            # Return Body
            if (not isinstance(returned, (str, bytes))
                    and returned is not None):
                # Return iterable object - from view.
                return returned
            else:
                # Return response object
                return resp

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
