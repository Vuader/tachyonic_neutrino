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
import re
from io import BytesIO

import tachyonic as root

from tachyonic.neutrino.threaddict import ThreadDict
from tachyonic.neutrino.strings import if_unicode_to_utf8
from tachyonic.neutrino.validate import is_text
from tachyonic.neutrino import constants as const
from tachyonic.neutrino import exceptions
from tachyonic.neutrino.wsgi.headers import Headers

log = logging.getLogger(__name__)

curl_session = ThreadDict()

if hasattr(root, 'debug'):
    debug = root.debug
else:
    debug = True


def _debug(debug_type, debug_msg):
    try:
        if is_text(str(debug_msg)):
            log.debug("(%d): %s" % (debug_type, str(debug_msg)))
        else:
            log.debug("(%d): Binary" % (debug_type))
    except UnicodeDecodeError:
        log.debug("(%d): Binary" % (debug_type))
        pass

class RestClient(object):
    def __init__(self, ssl_verify=False, ssl_verify_peer=True,
                 ssl_verify_host=True, ssl_cacert=None,
                 ssl_cainfo=None, timeout=30, connect_timeout=2,
                 ssl_cipher_list = None, username=None, password=None,
                 debug=debug):
        # Register Cleanup for use with Neutrino
        # However Neutrino is not always installed with restclient...
        try:
            import tachyonic.neutrino
            tachyonic.neutrino.app.register_cleanup(RestClient.close_all)
        except:
            pass

        self.ssl_cipher_list = ssl_cipher_list
        self.username = username
        self.password = password
        self.debug = debug

        if ssl_verify is True:
            if ssl_verify_peer is True:
                self.ssl_verify_peer = 1
            else:
                self.ssl_verify_peer = 0

            if ssl_verify_host is True:
                self.ssl_verify_host = 2
            else:
                self.ssl_verify_host = 0
        else:
                self.ssl_verify_peer = 0
                self.ssl_verify_host = 0

        self.ssl_cacert = ssl_cacert
        self.ssl_cainfo = ssl_cainfo
        self.timeout = timeout
        self.connect_timeout = connect_timeout

    def header_function(self, header_line):
        # HTTP standard specifies that headers are encoded in iso-8859-1.
        # On Python 2, decoding step can be skipped.
        # On Python 3, decoding step is required.
        header_line = header_line.decode('iso-8859-1')

        # Header lines include the first status line (HTTP/1.x ...).
        # We are going to ignore all lines that don't have a colon in them.
        # This will botch headers that are split on multiple lines...
        if ':' not in header_line:
            return

        # Break the header line into header name and value.
        name, value = header_line.split(':', 1)

        # Remove whitespace that may be present.
        # Header lines include the trailing newline, and
        # there may be whitespace around the colon.
        name = name.strip()
        value = value.strip()

        # Header names are case insensitive.
        # Lowercase name here.
        name = name.lower()

        # Now we can actually record the header name and value.
        self.server_headers[name] = value

    def get_host_port_from_url(self, url):
        url_splitted = url.split('/')
        host = "%s//%s" % (url_splitted[0], url_splitted[2])
        return host

    def execute(self, method, url, data=None, headers=[]):
        import pycurl
        host = self.get_host_port_from_url(url)
        if host in curl_session:
            curl = curl_session[host]
        else:
            curl_session[host] = pycurl.Curl()
            curl = curl_session[host]

        url = url.replace(" ", "%20")

        method = method.upper()

        self.server_headers = dict()

        buffer = BytesIO()

        curl.setopt(curl.URL, if_unicode_to_utf8(url))
        try:
            curl.setopt(curl.WRITEDATA, buffer)
        except TypeError:
            curl.setopt(curl.WRITEFUNCTION, buffer.write)

        curl.setopt(curl.HEADERFUNCTION, self.header_function)
        curl.setopt(curl.FOLLOWLOCATION, True)
        curl.setopt(curl.SSL_VERIFYPEER, self.ssl_verify_peer)
        curl.setopt(curl.SSL_VERIFYHOST, self.ssl_verify_host)

        if self.ssl_cipher_list is not None:
            curl.setopt(curl.SSL_CIPHER_LIST, self.ssl_cipher_list)

        curl.setopt(curl.CONNECTTIMEOUT, self.connect_timeout)
        curl.setopt(curl.TIMEOUT, self.timeout)
        curl.setopt(curl.TIMEOUT_MS, self.timeout*1000)

        if self.debug is True:
            curl.setopt(curl.DEBUGFUNCTION, _debug)
            curl.setopt(curl.VERBOSE, 1)

        if self.username is not None:
            curl.setopt(curl.USERNAME, self.username)

        if self.password is not None:
            curl.setopt(curl.PASSWORD, self.password)

        if data is not None:
            curl.setopt(curl.POSTFIELDS, if_unicode_to_utf8(data))
        else:
            curl.setopt(curl.POSTFIELDS, if_unicode_to_utf8(''))

        send_headers = list()
        for header in headers:
            send_header = if_unicode_to_utf8("%s: %s" % (header,
                                                                   headers[header]))
            send_headers.append(send_header)

        curl.setopt(pycurl.HTTPHEADER, send_headers)

        if method == const.HTTP_GET:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('GET'))
        elif method == const.HTTP_PUT:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('PUT'))
        elif method == const.HTTP_POST:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('POST'))
        elif method == const.HTTP_PATCH:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('PATCH'))
        elif method == const.HTTP_DELETE:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('DELETE'))
        elif method == const.HTTP_OPTIONS:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('OPTIONS'))
        elif method == const.HTTP_HEAD:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('HEAD'))
        elif method == const.HTTP_TRACE:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('TRACE'))
        elif method == const.HTTP_CONNECT:
            curl.setopt(curl.CUSTOMREQUEST,
                        if_unicode_to_utf8('CONNECT'))
        else:
            raise exceptions.RestClientError("Invalid request type %s" % (method,))

        try:
            curl.perform()
            status = curl.getinfo(pycurl.HTTP_CODE)
        except pycurl.error as e:
            del curl_session[host]
            if e[0] == 28:
                raise exceptions.RestClientError("Connection timeout %s (%s)" % (host,e))
            else:
                raise pycurl.error(e)

        # Figure out what encoding was sent with the response, if any.
        # Check against lowercased header name.
        encoding = None
        if 'content-type' in self.server_headers:
            content_type = self.server_headers['content-type'].lower()
            match = re.search('charset=(\S+)', content_type)
            if match:
                encoding = match.group(1)
        if encoding is None:
            # Default encoding for JSON is UTF-8.
            # Other content types may have different default encoding,
            # or in case of binary data, may have no encoding at all.
            encoding = 'utf_8'

        body = buffer.getvalue()
        # Decode using the encoding we figured out.
        body = body.decode(encoding)
        resp_header = Headers()
        for h in self.server_headers:
            resp_header[h] = self.server_headers[h]
        return (status, resp_header, body)

    @staticmethod
    def close_all():
        for session in curl_session:
            curl_session[session].close()
            if debug is True:
                log.debug("Closing session %s" % session)
        curl_session.clear()
