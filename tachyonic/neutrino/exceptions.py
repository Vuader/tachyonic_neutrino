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

from tachyonic.neutrino import constants as const

log = logging.getLogger(__name__)


class Error(Exception):
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description

    def __str__(self):
        return str(self.description)


class ValidationError(Error):
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description

    def __str__(self):
        return str(self.description)


class Authentication(ValidationError):
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description
        self.status = const.HTTP_403

    def __str__(self):
        return str(self.description)


class FieldError(ValidationError):
    def __init__(self, field, label, description, value):
        self.error = "%s %s %s" % (field, description, value)
        self.user = "%s %s %s" % (label, description, value)
        Exception.__init__(self, self.error)

    def __str__(self):
        return str(self.error)

    def user_error(self):
        return str(self.user)


class DoesNotExist(ValidationError):
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description

    def __str__(self):
        return str(self.description)


class FieldDoesNotExist(DoesNotExist):
    def __init__(self, field):
        Exception.__init__(self, field)
        self.field = field

    def __str__(self):
        return str(self.field)


class MultipleOblectsReturned(ValidationError):
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description

    def __str__(self):
        return str(self.description)


class RestClientError(Error):
    def __init__(self, description):
        Error.__init__(self, description)
        self.description = description

    def __str__(self):
        return str(self.description)


class ClientError(RestClientError):
    def __init__(self, title, description, status=const.HTTP_500):
        RestClientError.__init__(self, description)
        self.title = title
        self.description = description
        self.status = status

    def __str__(self):
        return str(self.description)


class HTTPError(Error):
    def __init__(self, status, title, description):
        Exception.__init__(self, description)
        if status is not None:
            self.status = status
        else:
            self.status = const.HTTP_500

        if title is not None:
            self.title = title
        else:
            self.title = status
        self.description = description
        self.headers = {}

    def __str__(self):
        if self.title is not None or self.description is not None:
            msg = ""
            if self.title is not None:
                msg += "%s: " % self.title
            if self.description is not None:
                msg += "%s" % self.description
        else:
            msg = self.status

        return str(msg)


class HTTPNotModified(HTTPError):
    """
    304 Not Modified.
    """

    def __init__(self):
        super(HTTPNotModified, self).__init__(const.HTTP_304, None, None)


class HTTPBadRequest(HTTPError):
    """
    400 Bad Request.
    """

    def __init__(self, title, description):
        super(HTTPBadRequest, self).__init__(const.HTTP_400, title, description)


class HTTPUnauthorized(HTTPError):
    """
    401 Unauthorized.
    """

    def __init__(self, title, description, challenges=None):
        super(HTTPUnauthorized, self).__init__(const.HTTP_401, title, description)

        if challenges is not None:
            self.headers['WWW-Authenticate'] = ', '.join(challenges)


class HTTPForbidden(HTTPError):
    """
    403 Forbidden.
    """

    def __init__(self, title, description):
        super(HTTPForbidden, self).__init__(const.HTTP_403, title, description)


class HTTPNotFound(HTTPError):
    """
    404 Not Found.
    """

    def __init__(self, title='Not found', description=None):
        super(HTTPNotFound, self).__init__(const.HTTP_404, title, description)


class HTTPMethodNotAllowed(HTTPError):
    """
    405 Method Not Allowed.
    """

    def __init__(self, allowed_methods=None):
        super(HTTPMethodNotAllowed, self).__init__(const.HTTP_405)
        if allowed_methods is not None:
            self.headers['Allow'] = ', '.join(allowed_methods)


class HTTPNotAcceptable(HTTPError):
    """
    406 Not Acceptable.
    """

    def __init__(self, description):
        super(HTTPNotAcceptable, self).__init__(const.HTTP_406, 'Media type not acceptable', description)


class HTTPConflict(HTTPError):
    """
    409 Conflict.
    """

    def __init__(self, title, description):
        super(HTTPConflict, self).__init__(const.HTTP_409, title, description)


class HTTPLengthRequired(HTTPError):
    """
    411 Length Required.
    """

    def __init__(self, title, description):
        super(HTTPLengthRequired, self).__init__(const.HTTP_411, title, description)


class HTTPPreconditionFailed(HTTPError):
    """
    412 Precondition Failed.
    """

    def __init__(self, title, description):
        super(HTTPPreconditionFailed, self).__init__(const.HTTP_412, title, description)


class HTTPUnsupportedMediaType(HTTPError):
    """
    415 Unsupported Media Type.
    """

    def __init__(self, description):
        super(HTTPUnsupportedMediaType, self).__init__(const.HTTP_415, 'Unsupported media type', description)


class HTTPUnprocessableEntity(HTTPError):
    """
    422 Unprocessable Entity.
    """

    def __init__(self, title, description):
        super(HTTPUnprocessableEntity, self).__init__(const.HTTP_422, title, description)


class HTTPTooManyRequests(HTTPError):
    """
    429 Too Many Requests.
    """

    def __init__(self, title, description):
        super(HTTPTooManyRequests, self).__init__(const.HTTP_429, title, description)


class HTTPUnavailableForLegalReasons(HTTPError):
    """
    451 Unavailable For Legal Reasons.
    """

    def __init__(self, title):
        super(HTTPUnavailableForLegalReasons, self).__init__(const.HTTP_451, title)


class HTTPInternalServerError(HTTPError):
    """
    500 Internal Server Error.
    """

    def __init__(self, title, description):
        super(HTTPInternalServerError, self).__init__(const.HTTP_500, title, description)


class HTTPBadGateway(HTTPError):
    """
    502 Bad Gateway.
    """

    def __init__(self, title, description):
        super(HTTPBadGateway, self).__init__(const.HTTP_502, title, description)


class HTTPServiceUnavailable(HTTPError):
    """
    503 Service Unavailable.
    """

    def __init__(self, title, description):
        super(HTTPServiceUnavailable, self).__init__(const.HTTP_503, title, description)


class HTTPInvalidHeader(HTTPBadRequest):
    """
    A header in the request is invalid.
    """

    def __init__(self, header_name):
        description = "The value provided for %s header is invalid." % header_name
        super(HTTPInvalidHeader, self).__init__('Invalid header value', description)


class HTTPMissingHeader(HTTPBadRequest):
    """
    A header is missing from the request.
    """

    def __init__(self, header_name):
        description = "Missing header value %s." % header_name
        super(HTTPMissingHeader, self).__init__('Missing header value', description)


class HTTPInvalidParam(HTTPBadRequest):
    """
    A parameter in the request is invalid.
    """

    def __init__(self, param_name):
        description = "The %s parameter is invalid." % param_name

        super(HTTPInvalidParam, self).__init__('Invalid parameter', description)


class HTTPMissingParam(HTTPBadRequest):
    """
    A parameter is missing from the request.
    """

    def __init__(self, param_name):
        description = "The %s parameter is missing." % param_name

        super(HTTPMissingParam, self).__init__('Missing parameter', description)
