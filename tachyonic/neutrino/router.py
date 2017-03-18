from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import re
import keyword

import tachyonic.neutrino

log = logging.getLogger(__name__)


def view(uri, method, req, resp):
    req.method = method
    method = method.upper()
    r = req.router._match(method, uri.strip('/'))
    if r is not None:
        route, obj_kwargs = r
        method, route, obj, name = route
        obj(req, resp, **obj_kwargs)
    else:
        raise tachyonic.neutrino.HTTPNotFound(description=uri)


class Router(object):
    def __init__(self):

        self.routes = []

    def view(self, uri, method, req, resp):
        view(uri, method, req, resp)

    def _match(self, method, request_uri):
        if "?" in request_uri:
            uri, args = request_uri.split('?')
            uri = uri.strip('/').split('/')
        else:
            uri = request_uri.split('/')

        for r in self.routes:
            r_method, r_uri, r_obj, r_name = r
            r_uri = r_uri.split('/')
            if method == r_method:
                if len(uri) == len(r_uri):
                    kwargs = {}
                    for (i, v) in enumerate(r_uri):
                        if len(v) > 0 and v[0] == '{':
                            v = v.replace('{', '').replace('}', '')
                            kwargs[v] = uri[i]
                        elif v != uri[i]:
                            break
                        if i+1 == len(r_uri):
                            return [r, kwargs]
        return None

    def route(self, req):
        uri = req.environ['PATH_INFO'].strip('/')
        if uri is None:
            uri = ''
        method = req.method
        return self._match(method, uri)

    def add(self, method, route, obj, name=None):
        if re.search('\s', route):
            raise ValueError('Route may not include whitespace.')
        fields = re.findall('{([^}]*)}', route)
        for field in fields:
            is_identifier = re.match('[A-Za-z_][A-Za-z0-9_]+$', field)
            if not is_identifier or field in keyword.kwlist:
                raise ValueError('Field names must be valid identifiers.')

        route = route.strip('/')
        if self._match(method, route) is None:
            r = list()
            r.append(method)
            r.append(route)
            r.append(obj)
            r.append(name)
            self.routes.append(r)
        else:
            raise tachyonic.neutrino.Error('Adding duplicate API route %s' % (route))
