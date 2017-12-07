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
import re
import keyword

from tachyonic.neutrino.wsgi.routing import CompiledRouter
from tachyonic.neutrino.exceptions import HTTPNotFound, DoesNotExist

log = logging.getLogger(__name__)


def view(uri, method, req, resp):
    """Open view based on URL and Method

    Args:
        uri (str): URI of resource. (exclude application entry point)
        method (str): HTTP Method. Use constants in
            tachyonic.neutrion.constants.
            * GET
            * POST
            * PUT
            * PATCH
            * DELETE
        req (object): Request Object.
        resp (object): Response Object.
    """
    req.method = method
    method = method.upper()
    r = req.router._falcon[method].find(uri)
    if r is not None:
        obj, methods, obj_kwargs, route, name = r
        return obj(req, resp, **obj_kwargs)
    else:
        raise HTTPNotFound(description=uri)


class Router(object):
    """ Simple Router Interface.

    The router is used to index and return views based on url and method.
    """

    def __init__(self):
        self._falcon = {}
        self._falcon['GET'] = CompiledRouter()
        self._falcon['POST'] = CompiledRouter()
        self._falcon['PUT'] = CompiledRouter()
        self._falcon['PATCH'] = CompiledRouter()
        self._falcon['DELETE'] = CompiledRouter()
        self.routes = []

    def view(self, uri, method, req, resp):
        """Open view based on URL and Method

        Args:
            uri (str): URI of resource. (exclude application entry point)
            method (str): HTTP Method. Use constants in
                tachyonic.neutrion.constants.
                * GET
                * POST
                * PUT
                * PATCH
                * DELETE
            req (object): Request Object.
            resp (object): Response Object.
        """
        view(uri, method, req, resp)

    def route(self, req):
        """Route based on Request Object.

        Returns view based on url and method in request object.
        """
        uri = req.environ['PATH_INFO'].strip('/')
        return self._falcon[req.method].find(uri)

    def find(self, method, uri):
        """Route based on Request Object.

        Search for a route that matches the given partial URI.

        Args:
            method (str): HTTP Method. Use constants in
                tachyonic.neutrion.constants.
                * GET
                * POST
                * PUT
                * PATCH
                * DELETE
            uri (str): The requested path to route.
        """
        if method in self._falcon:
            return self._falcon[method].find(uri)
        else:
            raise DoesNotExist(description = "Method %s not found")

    def add(self, methods, route, obj, name=None):
        """Add route to view.

        The route() method is used to associate a URI template with a resource.
        Neutrino then maps incoming requests to resources based on these templates.

        URI Template example: "/music/rock"

        If the route’s template contains field expressions, any responder that
        desires to receive requests for that route must accept arguments named
        after the respective field names defined in the template.

        A field expression consists of a bracketed field name.
        For example, given the following template:
            "/music/{genre}"

        The view would look like:
            def genre(self, req, resp, genre):

        Args:
            methods (list): List of Methods. Use constants in
                tachyonic.neutrion.constants.
                * GET
                * POST
                * PUT
                * PATCH
                * DELETE
            route (str): Route resource. (URI Template)
            obj (object): Actual view function or method.
            name (str): Used to identify policy to apply.
        """
        route = route.strip('/')
        self.routes.append((methods, route, obj, name))
        if not isinstance(methods, ( tuple, list)):
            methods = [ methods ]

        for method in methods:
            self._falcon[method].add_route(route, method, obj, name)
