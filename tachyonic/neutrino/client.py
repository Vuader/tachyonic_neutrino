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
import json
import datetime
from collections import OrderedDict
from decimal import Decimal

import tachyonic as root

from tachyonic.neutrino.threaddict import ThreadDict
from tachyonic.neutrino.restclient import RestClient
from tachyonic.neutrino import constants as const
from tachyonic.neutrino import exceptions
from tachyonic.neutrino.url import clean_url
from tachyonic.neutrino.strings import filter_none_text

log = logging.getLogger(__name__)

session = ThreadDict()

if hasattr(root, 'debug'):
    debug = root.debug
else:
    debug = True


class Client(RestClient):
    def __init__(self, url, timeout=1000, debug=debug):
        # Register Cleanup for use with Neutrino
        # However Neutrino is not always installed with client...
        try:
            import tachyonic.neutrino
            tachyonic.neutrino.app.register_cleanup(Client.close_all)
        except:
            pass

        self._endpoints = {}
        self.debug = debug
        self.url = url

        if url in session and 'endpoints' in session[url]:
            log.debug("Using existing session %s" % url)
            self.tachyonic_headers = session[url]['headers']
            self._endpoints = session[url]['endpoints']
            super(Client, self).__init__(timeout=timeout, debug=debug)
        else:
            log.debug("New session %s" % url)
            session[url] = {}
            session[url]['headers'] = {}
            super(Client, self).__init__(timeout=timeout, debug=debug)
            self.tachyonic_headers = session[url]['headers']
            self.tachyonic_headers = session[url]['endpoints'] = self.endpoints()
            self._endpoints = session[url]['endpoints']

    def _check_headers(self, server_headers, url):
        e = "Server not responding with JSON Content-Type %s" % url
        if 'content-type' in server_headers:
            if 'json' in server_headers['content-type'].lower():
                return True
            else:
                raise exceptions.ClientError('RESTAPI',
                                              e,
                                              const.HTTP_500)
        else:
            raise exceptions.ClientError('RESTAPI',
                                          e,
                                          const.HTTP_500)

    @staticmethod
    def close_all():
        for s in session:
            if debug is True:
                log.debug("Closing session %s" % s)
        session.clear()

    def endpoints(self):
        url = self.url
        try:
            server_status, server_headers, server_response = super(Client,
                                                                   self).execute(const.HTTP_GET,
                                                                                 url,
                                                                                 None,
                                                                                 [])
            self._check_headers(server_headers, url)
        except Exception as e:
            raise exceptions.ClientError('RESTAPI Retrieve Endpoints',
                                          e,
                                          const.HTTP_500)
        try:
            response = json.loads(server_response)
            self._endpoints = response['external']
            return self._endpoints
        except Exception as e:
            raise exceptions.ClientError('RESTAPI JSON Decode',
                                          e,
                                          const.HTTP_500)

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

    class _JsonEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Decimal):
                # Parse Decimal Value
                return str(o)
            elif isinstance(o, datetime.datetime):
                # Parse Datetime
                return str(o.strftime("%Y/%m/%d %H:%M:%S"))
            elif isinstance(o, bytes):
                return o.decode('utf-8')
            else:
                # Pass to Default Encoder
                return json.JSONEncoder.default(self,o)

    def execute(self, request, url, obj=None, headers=None, endpoint=None):
        import pycurl

        if obj is not None:
            # DETECT IF ORM
            if hasattr(obj, 'Meta'):
                data = obj.dump_json(indent=4)
            # DETECT IF REQUEST POST
            elif hasattr(obj, '_detected_post'):
                m = {}
                for field in obj:
                    m[field] = obj.get(field)
                data = json.dumps(m, indent=4, cls=self._JsonEncoder)
            else:
                log.error(obj)
                data = json.dumps(obj, indent=4, cls=self._JsonEncoder)
        else:
            data = None

        if endpoint is not None:
            if endpoint in self._endpoints:
                url = "%s/%s" % (self._endpoints[endpoint], url)
            else:
                http_status = const.HTTP_404
                title = "RESTAPI"
                desc = "Endpoint not found %s" % (endpoint,)
                raise exceptions.ClientError(title,
                                             desc,
                                             http_status)
        else:
            if self.url not in url:
                url = "%s/%s" % (self.url, url)
        url = clean_url(url)


        if headers is None:
            headers = self.tachyonic_headers
        else:
            headers.update(self.tachyonic_headers)

        try:
            status, server_headers, response = super(Client, self).execute(request, url, data, headers)
        except pycurl.error as e:
            raise exceptions.ClientError('RESTAPI CONNECT ERROR',
                                          e,
                                          const.HTTP_500)

        if status != 200:
            if 'content-type' in server_headers:
                if 'json' in server_headers['content-type'].lower():
                    if response is not None:
                        response = json.loads(response,
                                              object_pairs_hook=OrderedDict)
                        if 'error' in response:
                            response = response['error']
                            f = "HTTP_%s" % (str(status),)
                            if hasattr(const, f):
                                http_status = getattr(const, f)
                            else:
                                http_status = const.HTTP_500

                            title = "RESTAPI: %s" % (response['title'],)
                            raise exceptions.ClientError(filter_none_text(title),
                                                         filter_none_text(response['description']),
                                                         http_status)

        if response is not None:
            if ('content-type' in server_headers and
                    'json' not in server_headers['content-type'].lower()):
                pass
            else:
                try:
                    if response.strip() != '':
                        response = json.loads(response,
                                              object_pairs_hook=OrderedDict)
                    else:
                        response = None
                except Exception as e:
                    raise exceptions.ClientError('RESTAPI JSON Decode',
                                                  e,
                                                  const.HTTP_500)
        return [server_headers, response]
