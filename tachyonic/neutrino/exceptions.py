from __future__ import absolute_import, division, print_function, unicode_literals

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


class RestClientError(Error):
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description

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


class HTTPError(Error):
    def __init__(self, status, title, description):
        Exception.__init__(self, description)
        self.status = status
        self.title = title
        self.description = description
        self.headers = {}

    def __str__(self):
        return str(self.description)


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
