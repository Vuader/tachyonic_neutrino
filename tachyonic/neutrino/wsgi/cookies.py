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

log = logging.getLogger(__name__)

class Cookies(object):
    def __init__(self, req):
        self.req = req
        self.cookie = SimpleCookie()

        if 'HTTP_COOKIE' in req.environ:
            self.cookie.load(req.environ['HTTP_COOKIE'])

    def get(self, name, default=None):
        if name in self.cookie:
            return if_unicode_to_utf8(self.cookie[name].value)
        else:
            return default

    def set(self, name, value, expire=3600):
        host = self.req.get_host()

        self.cookie[name] = value

        host = self.req.get_host()

        if host is not None:
            self.cookie[name]['domain'] = host

        if expire is not None and expire != 0:
            self.cookie[name]['max-age'] = expire

    def __contains__(self, cookie):
        if cookie in self.cookie:
            return True
        else:
            return False

    def headers(self):
        h = []
        for cookie in self.cookie:
            h.append(('Set-Cookie',
                      self.cookie[cookie].OutputString()))
        return h

