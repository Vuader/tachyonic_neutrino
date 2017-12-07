# -*- coding: utf-8 -*-
# Copyright (c) 2017, Christiaan Frans Rademan.
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

from tachyonic.neutrino.threaddict import ThreadDict
from tachyonic.neutrino.restclient import RestClient
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.exceptions import RestClientError, ClientError
from tachyonic.neutrino.url import clean_url
from tachyonic.neutrino.strings import filter_none_text

log = logging.getLogger(__name__)

session = ThreadDict()

class Client(RestClient):
    def __init__(self, url, **kwargs):
        self._endpoints = {}
        self.url = url

        if url in session and 'endpoints' in session[url]:
            log.debug("Using existing session %s" % url)
            self.tachyonic_headers = session[url]['headers']
            self._endpoints = session[url]['endpoints']
            super(Client, self).__init__(**kwargs)
        else:
            log.debug("New session: %s" % url)
            session[url] = {}
            session[url]['headers'] = {}
            super(Client, self).__init__(**kwargs)
            self.tachyonic_headers = session[url]['headers']
            self.tachyonic_headers = session[url]['endpoints'] = self.endpoints()
            self._endpoints = session[url]['endpoints']

    @staticmethod
    def close_all():
        for s in session:
            log.debug("Closing session: %s" % s)
        session.clear()

    def endpoints(self):
        url = self.url
        try:
            status, headers, response = super(Client,
                                              self).execute(const.HTTP_GET,
                                              url)
        except Exception as e:
            raise ClientError('Retrieve Endpoints',
                              e,
                              500)

        self._endpoints = response['external']

        return self._endpoints

    def authenticate(self, username, password, domain):
        url = self.url
        auth_url = "%s/v1/token" % (url,)

        if 'X-Tenant-Id' in self.tachyonic_headers:
            del self.tachyonic_headers['X-Tenant-Id']
        if 'X-Auth-Token' in self.tachyonic_headers:
            del self.tachyonic_headers['X-Auth-Token']
        self.tachyonic_headers['X-Domain'] = domain

        data = {}
        data['username'] = username
        data['password'] = password
        data['expire'] = 1

        server_headers, result = self.execute("POST", auth_url,
                                              data, self.tachyonic_headers)

        if 'token' in result:
            self._token = result['token']
            self.tachyonic_headers['X-Auth-Token'] = self._token

        session[url]['headers'] = self.tachyonic_headers
        return result

    def token(self, token, domain, tenant_id):
        url = self.url
        auth_url = "%s/v1/token" % (url,)

        if tenant_id is not None:
            self.tachyonic_headers['X-Tenant-Id'] = tenant_id
        self.tachyonic_headers['X-Domain'] = domain
        self.tachyonic_headers['X-Auth-Token'] = token

        server_headers, result = self.execute("GET", auth_url,
                                              None)

        log.error(result)
        if 'token' in result:
            self.token = token
        else:
            if 'X-Tenant-Id' in self.tachyonic_headers:
                del self.tachyonic_headers['X-Tenant-Id']
            if 'X-Domain' in self.tachyonic_headers:
                del self.tachyonic_headers['X-Domain']
            if 'X-Auth-Token' in self.tachyonic_headers:
                del self.tachyonic_headers['X-Auth-Token']

        session[url]['headers'] = self.tachyonic_headers

        return result

    def domain(self, domain):
        self.tachyonic_headers['X-Domain'] = domain

    def tenant(self, tenant):
        if tenant is None:
            del self.tachyonic_headers['X-Tenant-Id']
        else:
            self.tachyonic_headers['X-Tenant-Id'] = tenant

    def execute(self, method, url,
                obj=None, headers=None, endpoint=None,
                encode=True, decode=True):

        if endpoint is not None:
            if endpoint in self._endpoints:
                url = "%s/%s" % (self._endpoints[endpoint], url)
            else:
                raise ClientError('Endpoint (%s)' % endpoint,
                                  'Endpoint not found',
                                  404)
        else:
            if self.url not in url:
                url = "%s/%s" % (self.url, url)
            endpoint = "Tachyonic"

        url = clean_url(url)

        if headers is None:
            headers = self.tachyonic_headers
        else:
            headers.update(self.tachyonic_headers)

        try:
            status, headers, response = super(Client,
                                              self).execute(method,
                                                            url,
                                                            obj,
                                                            headers,
                                                            encode=encode,
                                                            decode=decode)
        except RestClientError as e:
            raise ClientError('Endpoint (%s):' % endpoint,
                              e,
                              500)

        if status != 200:
            if isinstance(response, dict) and 'error' in response:
                if 'title' in response['error']:
                    title = "Endpoint (%s): %s" % (endpoint,
                                                   response['error']['title'],)
                else:
                    title = "Endpoint (%s):" % endpoint


                if 'description' in response['error']:
                    description = response['error']['description']
                else:
                    description = "Unknown error"

                raise ClientError(filter_none_text(title),
                                  filter_none_text(description),
                                  status)

        return [headers, response]
