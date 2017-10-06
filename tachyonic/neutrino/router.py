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
import re
import keyword

from tachyonic.neutrino.routing import CompiledRouter
from tachyonic.common.exceptions import HTTPNotFound

log = logging.getLogger(__name__)


def view(uri, method, req, resp):
    req.method = method
    method = method.upper()
    r = req.router._falcon.find(uri, req=method)
    if r is not None:
        obj, methods, obj_kwargs, route, name = r
        return obj(req, resp, **obj_kwargs)
    else:
        raise HTTPNotFound(description=uri)


class Router(object):
    def __init__(self):
        self._falcon = {}
        self._falcon['GET'] = CompiledRouter()
        self._falcon['POST'] = CompiledRouter()
        self._falcon['PUT'] = CompiledRouter()
        self._falcon['PATCH'] = CompiledRouter()
        self._falcon['DELETE'] = CompiledRouter()
        self.routes = []

    def view(self, uri, method, req, resp):
        view(uri, method, req, resp)

    def route(self, req):
        uri = req.environ['PATH_INFO']
        return self._falcon[req.method].find(uri)

    def add(self, methods, route, obj, name=None):
        self.routes.append((methods, route, obj, name))
        if not isinstance(methods, ( tuple, list)):
            methods = [ methods ]

        for method in methods:
            self._falcon[method].add_route(route, method, obj, name)
