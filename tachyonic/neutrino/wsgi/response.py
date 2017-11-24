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
import datetime

from io import StringIO, BytesIO

from tachyonic.neutrino import exceptions
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.wsgi.headers import Headers
from tachyonic.neutrino.strings import if_unicode_to_utf8
from tachyonic.neutrino.dt import utc_time
from tachyonic.neutrino.wsgi import router

log = logging.getLogger(__name__)


def http_moved_permanently(url, req, resp):
    """ 301 Moved Permanently.

    The HTTP response status code 301 Moved Permanently is used
    for permanent URL redirection, meaning current links or records
    using the URL that the response is received for should be updated.
    The new URL should be provided in the Location field included with
    the response. The 301 redirect is considered a best practice for
    upgrading users from HTTP to HTTPS.

    Args:
        url (str): Redirected to URL.
        req (obj): Request Object. (req)
        resp (obj): Response Object. (resp)
    """

    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_301
    resp.headers['Location'] = url


def http_found(url, req, resp):
    """ 302 Found.

    The HTTP response status code 302 Found is a common way of
    performing URL redirection.

    An HTTP response with this status code will additionally provide
    a URL in the header field location. The user agent (e.g. a web browser)
    is invited by a response with this code to make a second, otherwise
    identical, request to the new URL specified in the location field.
    The HTTP/1.0 specification (RFC 1945) initially defined this code,
    and gives it the description phrase "Moved Temporarily".

    Many web browsers implemented this code in a manner that violated
    this standard, changing the request type of the new request to GET,
    regardless of the type employed in the original request (e.g. POST).
    For this reason, HTTP/1.1 (RFC 2616) added the new status codes 303
    and 307 to disambiguate between the two behaviours, with 303 mandating
    the change of request type to GET, and 307 preserving the request
    type as originally sent. Despite the greater clarity provided by this
    disambiguation, the 302 code is still employed in web frameworks to
    preserve compatibility with browsers that do not implement the
    HTTP/1.1 specification.

    As a consequence, the update of RFC 2616 changes the definition to
    allow user agents to rewrite POST to GET.

    Args:
        url (str): Redirected to URL.
        req (obj): Request Object. (req)
        resp (obj): Response Object. (resp)
    """
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_302
    resp.headers['Location'] = url


def http_see_other(url, req, resp):
    """ 303 See Other.

    The HTTP response status code 303 See Other is a way to redirect
    web applications to a new URI, particularly after a HTTP POST has
    been performed, since RFC 2616 (HTTP 1.1).

    According to RFC 7231, which obsoletes RFC 2616, "A 303 response to
    a GET request indicates that the origin server does not have a
    representation of the target resource that can be transferred by the
    server over HTTP. However, the Location field value refers to a resource
    that is descriptive of the target resource, such that making a retrieval
    request on that other resource might result in a representation that is
    useful to recipients without implying that it represents the original
    target resource."

    This status code should be used with the location header, as described
    below. If a server responds to a POST or other non-idempotent request
    with a 303 See Other response and a value for the location header, the
    client is expected to obtain the resource mentioned in the location
    header using the GET method; to trigger a request to the target resource
    using the same method, the server is expected to provide a 307 Temporary
    Redirect response.

    303 See Other has been proposed as one way of responding to a request for
    a URI that identifies a real-world object according to Semantic Web theory
    (the other being the use of hash URIs). For example,
    if http://www.example.com/id/alice identifies a person, Alice, then it would
    be inappropriate for a server to respond to a GET request with 200 OK, as
    the server could not deliver Alice herself. Instead the server would issue a
    303 See Other response which redirected to a separate URI providing a
    description of the person Alice.

    303 See Other can be used for other purposes. For example, when building a
    RESTful web API that needs to return to the caller immediately but continue
    executing asynchronously (such as a long-lived image conversion), the web
    API can provide a status check URI that allows the original client who
    requested the conversion to check on the conversion's status. This status
    check web API should return 303 See Other to the caller when the task is
    complete, along with a URI from which to retrieve the result in the Location
    HTTP header field.

    Args:
        url (str): Redirected to URL.
        req (obj): Request Object. (req)
        resp (obj): Response Object. (resp)
    """
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_303
    resp.headers['Location'] = url


def http_temporary_redirect(url, req, resp):
    """ 307 Temporary Redirect.

    The target resource resides temporarily under a different URI and the
    user agent MUST NOT change the request method if it performs an automatic
    redirection to that URI.

    Since the redirection can change over time, the client ought to continue
    using the original effective request URI for future requests.

    The server SHOULD generate a Location header field in the response
    containing a URI reference for the different URI. The user agent MAY use
    the Location field value for automatic redirection. The server's response
    payload usually contains a short hypertext note with a hyperlink to the
    different URI(s).

    Note: This status code is similar to 302 Found, except that it does not
    allow changing the request method from POST to GET. This specification
    defines no equivalent counterpart for 301 Moved Permanently (RFC7238, however,
    proposes defining the status code 308 Permanent Redirect for this purpose).

    Args:
        url (str): Redirected to URL.
        req (obj): Request Object. (req)
        resp (obj): Response Object. (resp)
    """
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_307
    resp.headers['Location'] = url


def http_permanent_redirect(url, req, resp):
    """ 308 Permanent Redirect.

    The target resource has been assigned a new permanent URI and any future
    references to this resource ought to use one of the enclosed URIs.

    Clients with link editing capabilities ought to automatically re-link
    references to the effective request URI1 to one or more of the new
    references sent by the server, where possible.

    The server SHOULD generate a Location header field in the response
    containing a preferred URI reference for the new permanent URI. The
    user agent MAY use the Location field value for automatic redirection.
    The server's response payload usually contains a short hypertext note
    with a hyperlink to the new URI(s).

    A 308 response is cacheable by default; i.e., unless otherwise indicated
    by the method definition or explicit cache controls.

    Note: This status code is similar to 301 Moved Permanently, except that
    it does not allow changing the request method from POST to GET.

    Args:
        url (str): Redirected to URL.
        req (obj): Request Object. (req)
        resp (obj): Response Object. (resp)
    """
    resp.clear()
    if 'http' not in url.lower():
        app = req.get_app_url()
        url = url.strip('/')
        url = "%s/%s" % (app, url)
    resp.status = const.HTTP_308
    resp.headers['Location'] = url


class Response(object):
    """ WSGI Response

    When a page is requested, Neutrino creates an Response object that
    used to form the response. Then Neutrino loads the appropriate
    view, passing the Response as the second argument to the middleware and
    view function.

    The Response object represents the application’s HTTP response to the
    request. It provides properties and methods for setting status, header
    and body data. 

    Args:
        req (Request): Request Object.

    Attributes:
        headers: Response headers (dictionary object)
        router: Router object.
        content_length: Response size. (read-only)
        body: Set only response body.
    """
    _attributes = ['status']

    def __init__(self, req=None):
        self.status = const.HTTP_200
        super(Response, self).__setattr__('headers', Headers())
        super(Response, self).__setattr__('_io', BytesIO())
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_req', req)

        # Default Headers
        self.headers['Content-Type'] = const.TEXT_HTML
        self.headers['X-Powered-By'] = 'Tachyonic'
        self.headers['X-Request-ID'] = self._req.request_id

        # CACHING
        now = utc_time()
        now = datetime.datetime.strftime(now, "%a, %d %b %Y %H:%M:%S GMT")
        self.headers['Last-Modified'] = now

    def __setattr__(self, name, value):
        if name in self._attributes:
            super(Response, self).__setattr__(name, value)
        elif name == 'body':
            self.clear()
            super(Response, self).__setattr__('_io', BytesIO())
            self.write(value)
        else:
            AttributeError("'response' object can't bind" +
                           " attribute '%s'" % (name,))

    def modified(self, datetime_obj):
        """ Set content modified GMT date and time.

        If date and time is equel to the value in the client (browser) cache,
        the content will not be returned. a HTTP 304 Not Modified is sent and the
        client cache is used.

        Args:
            datetime_obj (datetime.datatime): Last modified datatime object.
        """
        modified_datetime = datetime.datetime.strftime(datetime_obj, "%a, %d %b %Y %H:%M:%S GMT")
        self.headers['Last-Modified'] = str(modified_datetime)
        if modified_datetime == self._req.cached:
            raise exceptions.HTTPNotModified()

    def seek(self, position):
        """Change stream position.

        Seek to byte offset pos relative to position indicated by whence:
            0  Start of stream (the default).  pos should be >= 0;
            1  Current position - pos may be negative;
            2  End of stream - pos usually negative.

        Returns the new absolute position.
        """
        return self._io.seek(position)

    def read(self, size=0):
        """Read at most size bytes, returned as a bytes object.

        If the size argument is negative, read until EOF is reached.
        Return an empty bytes object at EOF.

        Returns content of response body.
        """
        if size == 0:
            return self._io.read()
        else:
            return self._io.read(size)

    def readline(self, size=0):
        """Next line from the file, as a bytes object.

        Retain newline.  A non-negative size argument limits the maximum
        number of bytes to return (an incomplete line may be returned then).
        Return an empty bytes object at EOF.

        Returns one line content of response body.
        """
        if size == 0:
            return self._io.readline()
        else:
            return self._io.readline(size)

    def write(self, data):
        """Write bytes to response body.

        Return the number of bytes written.
        """
        data = if_unicode_to_utf8(data)

        super(Response, self).__setattr__('content_length',
                                          self._io.write(data)+self.content_length)
        self.headers['Content-Length'] = str(self.content_length)

        return self.content_length

    def clear(self):
        """Clear response body"""
        del self.headers['Content-Length']
        super(Response, self).__setattr__('content_length', 0)
        super(Response, self).__setattr__('_io', BytesIO())

    def __iter__(self):
        self._io.seek(0)
        return response_io_stream(self._io)

    def view(self, url, method):
        """Open Alternate View

        Args:
            url (str): Redirected to URL.
            method (str): HTTP Method for example constants.HTTP_POST.
        """
        self.clear()
        router.view(url, method, self._req, self)

    def redirect(self, url):
        """Redirect to URL

        The HTTP response status code 303 See Other is a way to redirect
        web applications to a new URI, particularly after a HTTP POST has
        been performed, since RFC 2616 (HTTP 1.1).

        Args:
            url (str): Redirected to URL.
        """
        self.clear()
        http_see_other(url, self._req, self)

    def wsgi_headers(self):
        """Return headers for WSGI

        HTTP headers expected by the client
        They must be wrapped as a list of tupled pairs:
            [(Header name, Header value)].
        """

        return self.headers.wsgi_headers() + self._req.cookies.wsgi_headers()


def response_io_stream(f, chunk_size=None):
    '''
    Response payload iterable object.

    response_io_stream should only be used in situations where it is absolutely
    required that the whole content isn’t iterated before transferring the data
    to the client. Content-Length headers can’t be generated for streaming
    responses.

    Args:
        f (object): Iterable object.
        chunk_size (int): Amount of bytes to yield at a time.
    '''
    while True:
        if chunk_size is None:
            chunk = f.read()
        else:
            chunk = f.read(chunk_size)
        if not chunk:
            break
        yield if_unicode_to_utf8(chunk)
