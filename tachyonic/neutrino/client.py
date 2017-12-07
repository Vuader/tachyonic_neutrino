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

from tachyonic.neutrino.http.headers import status_codes
from tachyonic.neutrino.threaddict import ThreadDict
from tachyonic.neutrino.restclient import RestClient
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.exceptions import RestClientError, ClientError
from tachyonic.neutrino.url import clean_url
from tachyonic.neutrino.strings import filter_none_text

log = logging.getLogger(__name__)

session = ThreadDict()

class Client(RestClient):
    """Tachyonic RestApi Client.

    Client wrapped around RestClient using python requests.

    Provided for convienace to using RESTful API.

    Provides simple authentication methods and tracks endpoints.
    Keeps connection to specfici host, port open and acts like a singleton
    providing each thread continues request apabilities without reconnecting.

    Args:
        url (str): URL of Tachyonic main endpoint API.
        timeout (float/tuple): How many seconds to wait for the server to send
            data before giving up, as a float, or a (connect timeout, read
            read timeout) tuple. Defaults to (8, 2) (optional)
        auth (tuple): Auth tuple to enable Basic/Digest/Custom HTTP Auth.
            ('username', 'password' ) pair.
        verify (str/bool): Either a boolean, in which case it controls whether
            we verify the server's TLS certificate, or a string, in which case
            it must be a path to a CA bundle to use. Defaults to True.
            (optional)
        cert (str/tuple): if String, path to ssl client cert file (.pem). If
            Tuple, ('cert', 'key') pair.
    """
    def __init__(self, url, **kwargs):
        self._endpoints = {}
        self._url = url

        if url in session and 'endpoints' in session[url]:
            log.debug("Using existing session %s" % url)
            self._tachyonic_headers = session[url]['headers']
            self._endpoints = session[url]['endpoints']
            super(Client, self).__init__(**kwargs)
        else:
            log.debug("New session: %s" % url)
            session[url] = {}
            session[url]['headers'] = {}
            super(Client, self).__init__(**kwargs)
            self._tachyonic_headers = session[url]['headers']
            session[url]['endpoints'] = self._collect_endpoints()
            self._endpoints = session[url]['endpoints']

    @staticmethod
    def close_all():
        """Close all sessions for thread.
        """
        for s in session:
            log.debug("Closing session: %s" % s)
        session.clear()

    def _collect_endpoints(self):
        url = self._url
        try:
            status, headers, response = super(Client,
                                              self).execute(const.HTTP_GET,
                                              url)
        except Exception as e:
            raise ClientError('Retrieve Endpoints',
                              e,
                              500)

        if 'external' in response:
            return response['external']
        else:
            raise ClientError('Retrieve Endpoints',
                              'Invalid API Response.',
                              500)

    def authenticate(self, username, password, domain):
        """Authenticate using credentials.

        Once authenticated execute will be processed using the context
        relative to user credentials.

        Args:
            username (str): Username.
            password (str): Password.
            domain (str): Name of domain for context.

        Returns authenticated result.
        """
        auth_url = "%s/v1/token" % (self._url,)

        if 'X-Tenant-Id' in self._tachyonic_headers:
            del self._tachyonic_headers['X-Tenant-Id']
        if 'X-Auth-Token' in self._tachyonic_headers:
            del self._tachyonic_headers['X-Auth-Token']
        self._tachyonic_headers['X-Domain'] = domain

        data = {}
        data['username'] = username
        data['password'] = password
        data['expire'] = 1

        headers, result = self.execute("POST", auth_url,
                                       data, self._tachyonic_headers)

        if 'token' in result:
            self._token = result['token']
            self._tachyonic_headers['X-Auth-Token'] = self._token

        return result

    def token(self, token, domain, tenant_id=None):
        """Authenticate using Token.

        Once authenticated execute will be processed using the context
        relative to user credentials.

        Args:
            token (str): Token Key.
            domain (str): Name of domain for context.
            tenant_id (str): Tenant id for context. (optional)

        Returns authenticated result.
        """
        auth_url = "%s/v1/token" % (self._url,)

        if tenant_id is not None:
            self._tachyonic_headers['X-Tenant-Id'] = tenant_id
        elif 'X-Tenant-Id' in self._tachyonic_headers:
            del self._tachyonic_headers['X-Tenant-Id']

        headers, result = self.execute("GET", auth_url)

        if 'token' in result:
            self.token = token
            self._tachyonic_headers['X-Domain'] = domain
            self._tachyonic_headers['X-Auth-Token'] = token
        else:
            if 'X-Tenant-Id' in self._tachyonic_headers:
                del self._tachyonic_headers['X-Tenant-Id']
            if 'X-Domain' in self._tachyonic_headers:
                del self._tachyonic_headers['X-Domain']
            if 'X-Auth-Token' in self._tachyonic_headers:
                del self._tachyonic_headers['X-Auth-Token']

        return result

    def domain(self, domain):
        """Set context of domain name.
        """
        self._tachyonic_headers['X-Domain'] = domain

    def tenant(self, tenant):
        """Set context of tenant unique id.
        """
        if tenant is None:
            del self.tachyonic_headers['X-Tenant-Id']
        else:
            self._tachyonic_headers['X-Tenant-Id'] = tenant

    def execute(self, method, resource,
                obj=None, headers=None, endpoint=None,
                encode=True, decode=True):
        """Execute Request.

        Args:
            method (str): method for the request.
                * GET - The GET method requests a representation of the
                  specified resource. Requests using GET should only
                  retrieve data.
                * POST - The POST method is used to submit an entity to the
                  specified resource, often causing a change in state or side
                  effects on the server
                * PUT - The PUT method replaces all current representations of
                  the target resource with the request payload.
                * PATCH - The PATCH method is used to apply partial
                  modifications to a resource.
                * DELETE - The DELETE method deletes the specified resource.
                * HEAD - The HEAD method asks for a response identical to
                  that of a GET request, but without the response body.
                * CONNECT - The CONNECT method establishes a tunnel to the
                  server identified by the target resource.
                * OPTIONS - The OPTIONS method is used to describe the
                  communication options for the target resource.
                * TRACE - The TRACE method performs a message loop-back test
                  along the path to the target resource.
            Resource (str): Path for Resource on API.
            obj (obj): str, dict or list to be converted to JSON if encode is
                True. Otherwise sent as clear text. Objects with json method
                will be used to return json.
            headers (dict): HTTP Headers to send with the request.
            encode (bool): Encode request body as JSON where possible.
            decode (bool): Decode response body as JSON where possible.

        Response body will be string unless json data is decoded either
        a list or dict will be returned.

        Returns tuple (status code, respone headers, response body)
        """

        if endpoint is not None:
            if endpoint in self._endpoints:
                resource = "%s/%s" % (self._endpoints[endpoint], resource)
            else:
                raise ClientError('Endpoint (%s)' % endpoint,
                                  'Endpoint not found',
                                  404)
        else:
            if self._url not in resource:
                resource = "%s/%s" % (self._url, resource)
            endpoint = "Tachyonic"

        resource = clean_url(resource)

        if headers is None:
            headers = self._tachyonic_headers
        else:
            headers.update(self._tachyonic_headers)

        try:
            status, headers, response = super(Client,
                                              self).execute(method,
                                                            resource,
                                                            obj,
                                                            headers,
                                                            encode=encode,
                                                            decode=decode)
        except RestClientError as e:
            raise ClientError('Endpoint (%s):' % endpoint,
                              e,
                              500)

        if status >= 400:
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
            else:
                raise ClientError('%s %s' % (status, status_codes[status]),
                                  None,
                                  status)

        return [headers, response]
