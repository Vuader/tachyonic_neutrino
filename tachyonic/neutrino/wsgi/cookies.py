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
from http.cookies import SimpleCookie

from tachyonic.neutrino.strings import if_unicode_to_utf8
from tachyonic.neutrino.exceptions import DoesNotExist

log = logging.getLogger(__name__)

class Cookies(object):
    """HTTP Cookies Interface.
    
    Provide a simple interface for creating, modifying, and rendering
    individual HTTP cookies.

    A dictionary like object containing all cookies. Keys and values are
    strings.

    Args:
        req (object): Request Object (tachyonic.neutrino.wsgi.request.Request)
    """
    def __init__(self, req):
        self.req = req
        self.cookie = SimpleCookie()

        if 'HTTP_COOKIE' in req.environ:
            self.cookie.load(req.environ['HTTP_COOKIE'])

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, cookie):
        if cookie in self.cookie:
            return True
        else:
            return False

    def __iter__(self):
        return iter(self.cookie)

    def get(self, name, default=None):
        """Returns a cookie value for a cookie,

        Args:
            name (str): Cookie Name
            default (str): Default Value
        """
        if name in self.cookie:
            return if_unicode_to_utf8(self.cookie[name].value)
        else:
            if default is not None:
                return default
            else:
                raise DoesNotExist('Cookie not found %s' % name)

    def set(self, name, value, max_age=3600):
        """ Sets a cookie.

        Args:
            name (str): Cookie Name
            value (str): Cookie Value
            max_age (int): should be a number of seconds, or None (default) if
                the cookie should last only as long as the client’s browser
                session. Expires will be calculated.
        """
        self.cookie[name] = value

        host = self.req.get_host()

        if host is not None:
            self.cookie[name]['domain'] = host

        if max_age is not None and max_age != 0:
            self.cookie[name]['max-age'] = max_age

    def wsgi_headers(self):
        """Return multiple cookie headers for WSGI

        HTTP headers expected by the client
        They must be wrapped as a list of tupled pairs:
            [(Header name, Header value)].
        """
        h = []
        for cookie in self.cookie:
            h.append(('Set-Cookie',
                      self.cookie[cookie].OutputString()))
        return h
