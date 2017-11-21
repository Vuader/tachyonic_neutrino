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

import sys


class _Constant(object):
    class ConstError(TypeError):
        pass

    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise self.ConstError("Can't rebind constant(%s)" % key)
        self.__dict__[key] = value


_const = _Constant()

_const.TEXT_HTML = 'text/html; charset=UTF-8'
_const.TEXT_PLAIN = 'text/plain; charset=UTF-8'
_const.TEXT_CSS = 'text/css; charset=UTF-8'
_const.IMAGE_JPEG = 'image/jpeg'
_const.IMAGE_GIF = 'image/gif'
_const.IMAGE_PNG = 'image/png'
_const.APPLICATION_XML = 'application/xml; charset=UTF-8'
_const.APPLICATION_JSON = 'application/json; charset=UTF-8'
_const.APPLICATION_OCTET_STREAM = 'application/octet-stream'
_const.APPLICATION_FORM_DATA = 'application/x-www-form-urlencoded'
_const.APPLICATION_PDF = 'application/pdf'

_const.HTTP_GET = 'GET'
_const.HTTP_POST = 'POST'
_const.HTTP_PUT = 'PUT'
_const.HTTP_DELETE = 'DELETE'
_const.HTTP_PATCH = 'PATCH'
_const.HTTP_OPTIONS = 'OPTIONS'
_const.HTTP_HEAD = 'HEAD'
_const.HTTP_TRACE = 'TRACE'
_const.HTTP_CONNECT = 'CONNECT'

_const.HTTP_100 = '100 Continue'
_const.HTTP_101 = '101 Switching Protocols'
_const.HTTP_200 = '200 OK'
_const.HTTP_201 = '201 Created'
_const.HTTP_202 = '202 Accepted'
_const.HTTP_203 = '203 Non-Authoritative Information'
_const.HTTP_204 = '204 No Content'
_const.HTTP_205 = '205 Reset Content'
_const.HTTP_206 = '206 Partial Content'
_const.HTTP_226 = '226 IM Used'
_const.HTTP_300 = '300 Multiple Choices'
_const.HTTP_301 = '301 Moved Permanently'
_const.HTTP_302 = '302 Found'
_const.HTTP_303 = '303 See Other'
_const.HTTP_304 = '304 Not Modified'
_const.HTTP_305 = '305 Use Proxy'
_const.HTTP_306 = '306 Switch Proxy'
_const.HTTP_307 = '307 Temporary Redirect'
_const.HTTP_308 = '308 Permanent Redirect'
_const.HTTP_400 = '400 Bad Request'
_const.HTTP_401 = '401 Unauthorized'  # <-- Really means "unauthenticated"
_const.HTTP_402 = '402 Payment Required'
_const.HTTP_403 = '403 Forbidden'  # <-- Really means "unauthorized"
_const.HTTP_404 = '404 Not Found'
_const.HTTP_405 = '405 Method Not Allowed'
_const.HTTP_406 = '406 Not Acceptable'
_const.HTTP_407 = '407 Proxy Authentication Required'
_const.HTTP_408 = '408 Request Time-out'
_const.HTTP_409 = '409 Conflict'
_const.HTTP_410 = '410 Gone'
_const.HTTP_411 = '411 Length Required'
_const.HTTP_412 = '412 Precondition Failed'
_const.HTTP_413 = '413 Payload Too Large'
_const.HTTP_414 = '414 URI Too Long'
_const.HTTP_415 = '415 Unsupported Media Type'
_const.HTTP_416 = '416 Range Not Satisfiable'
_const.HTTP_417 = '417 Expectation Failed'
_const.HTTP_418 = "418 I'm a teapot"
_const.HTTP_422 = "422 Unprocessable Entity"
_const.HTTP_426 = '426 Upgrade Required'
_const.HTTP_428 = '428 Precondition Required'
_const.HTTP_429 = '429 Too Many Requests'
_const.HTTP_431 = '431 Request Header Fields Too Large'
_const.HTTP_451 = '451 Unavailable For Legal Reasons'
_const.HTTP_500 = '500 Internal Server Error'
_const.HTTP_501 = '501 Not Implemented'
_const.HTTP_502 = '502 Bad Gateway'
_const.HTTP_503 = '503 Service Unavailable'
_const.HTTP_504 = '504 Gateway Time-out'
_const.HTTP_505 = '505 HTTP Version not supported'
_const.HTTP_511 = '511 Network Authentication Required'

_const.BLOWFISH = 1
_const.MD5 = 2
_const.SHA256 = 3
_const.SHA512 = 4
_const.CLEARTEXT = 5
_const.LDAP_BLOWFISH = 6
_const.LDAP_MD5 = 7
_const.LDAP_SMD5 = 8
_const.LDAP_SHA1 = 9
_const.LDAP_SSHA1 = 10
_const.LDAP_SHA256 = 11
_const.LDAP_SHA512 = 12
_const.LDAP_CLEARTEXT = 13

_const.LEFT = 1
_const.RIGHT = 2

sys.modules[__name__] = _const
