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
import requests
from collections import OrderedDict

from tachyonic.neutrino import __version__
from tachyonic.neutrino.threaddict import ThreadDict
from tachyonic.neutrino.strings import if_unicode_to_utf8
from tachyonic.neutrino.validate import is_text
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.exceptions import RestClientError
from tachyonic.neutrino.http.headers import status_codes, Headers
from tachyonic.neutrino.url import host_url
from tachyonic.neutrino import js

log = logging.getLogger(__name__)

req_session = ThreadDict()

def _debug(method, url, payload, request_headers, response_headers,
           response, status_code):
    if log.getEffectiveLevel() <= logging.DEBUG:
        log.debug('Method: %s, URL: %s (%s %s)' % (method,
                                                url,
                                                status_code,
                                                status_codes[status_code]))
        log.debug('Request Headers: %s' % request_headers)
        log.debug('Response Headers: %s' % response_headers)
        if is_text(payload):
            if isinstance(payload, bytes):
                payload = payload.decode('UTF-8')
            payload = payload.split('\n')
            for l, p in enumerate(payload):
                log.debug('Request Payload (%s): %s' % (l, p))
        else:
            log.debug('Request Payload: BINARY')

        if is_text(response):
            response = response.decode('UTF-8').split('\n')
            for l, p in enumerate(response):
                log.debug('Response Payload (%s): %s' % (l, p))
        else:
            log.debug('Response Payload: BINARY')

class RestClient(object):
    """HTTP Python Requests Wrapper.

    Provided for convienace to using RESTful API.

    Keeps connection to specfici host, port open and acts like a singleton
    providing each thread continues request apabilities without reconnecting.

    Args:
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
    def __init__(self, timeout=(8, 2),
                 auth=None, verify=True,
                 cert=None):

        self.auth = auth
        self.timeout = (30, 2)
        self.verify = verify
        self.cert = cert

    def _parse_data(self, data):
        """Format Data for request body.
        """
        if data is not None:
            if hasattr(data, 'json'):
                data = data.json()
            elif isinstance(data, (dict, list, OrderedDict)):
                data = js.dumps(data)

        return if_unicode_to_utf8(data)

    def execute(self, method, url, data=None,
                headers={}, encode=True, decode=True):
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
            url (str): URL for the new request.
            data (obj): str, dict or list to be converted to JSON if encode is
                True. Otherwise sent as clear text. Objects with json method
                will be used to return json.
            headers (dict): HTTP Headers to send with the request.
            encode (bool): Encode request body as JSON where possible.
            decode (bool): Decode response body as JSON where possible.

        Response body will be string unless json data is decoded either
        a list or dict will be returned.

        Returns tuple (status code, respone headers, response body)
        """
        if encode is True:
            data = self._parse_data(data)

        host = host_url(url)

        if host in req_session:
            log.debug("Using existing session: %s" % host)
            session = req_session[host]
        else:
            log.debug("New session: %s" % host)
            req_session[host] = requests.Session()
            session = req_session[host]

        if data is None:
            data = ''

        headers['User-Agent'] = 'Tachyonic Neutrino v%s (RESTful API Client)' % __version__
        headers['Content-Length'] = str(len(data))
        req = requests.Request(method.upper(),
                               url,
                               data=data,
                               headers=headers,
                               auth=self.auth)

        session_request = session.prepare_request(req)

        try:
            resp = session.send(session_request,
                               timeout=self.timeout,
                               verify=self.verify,
                               cert=self.cert)
            _debug(method, url, data, headers, resp.headers,
                   resp.content, resp.status_code)

        except requests.ConnectionError as e:
            raise RestClientError('Connection error %s' % e)
        except requests.HTTPError as e:
            raise RestClientError('HTTP error %s' % e)
        except requests.ConnectTimeout as e:
            raise RestClientError('Connect timeout %s' % e)
        except requests.ReadTimeout as e:
            raise RestClientError('Read timeout %s' % e)
        except requests.Timeout as e:
            raise RestClientError('Timeout %s' % e)

        if ('content-type' in resp.headers and
                'application/json' in resp.headers['content-type'].lower() and
                decode is True):

            if resp.encoding.upper() != 'UTF-8':
                raise RestClientError('JSON requires UTF-8 Encoding')

            try:
                if resp.status_code != 204:
                    return (resp.status_code,
                            resp.headers,
                            js.loads(resp.content))
                else:
                    return (resp.status_code,
                            resp.headers,
                            b'')
            except Exception as e:
                raise RestClientError('JSON Decode: %s' % e)

        return (resp.status_code,
                resp.headers,
                resp.content)

    @staticmethod
    def close_all():
        """Close all sessions for thread.
        """
        for session in req_session:
            req_session[session].close()
            log.debug("Closing session: %s" % session)
        req_session.clear()
