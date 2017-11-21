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

log = logging.getLogger(__name__)


class Error(object):
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
        if isinstance(e, exceptions.HTTPError) or isinstance(e, exceptions.ClientError):
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
        else:
            title = const.HTTP_500
            description = repr(e)
            code = 500
            resp.status = const.HTTP_500

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