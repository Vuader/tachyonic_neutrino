.. _error:

Error Handling
==============

Exceptions
----------
Tachyon raises some of its own exceptions as well as standard Python exceptions.
Some exceptions when raised, generate a http/json errors automatically depending on the content_type set in the header.

You can raise some of these exceptions yourself with in the views for desired affect.

**Validation Error**
 *tachyon.ValidationError*

 The ValidationError exception is raised when data fails form or model field validation.

**FieldError**
 *tachyon.FieldError*

 The FieldError exception is raised when there is a problem with a model field.

**DoesNotExist**
 *tachyon.DoesNotExist*

 The base class for DoesNotExist exceptions.

**FieldDoesNotExist**
 *tachyon.FieldDoesNotExist*

 The FieldDoesNotExist exception is raised by a model when the field does not exist.

**MultipleObjectsReturned**
 *tachyon.MultipleObjectsReturned*

 The MultipleObjectsReturned exception is raised by a query if only one object is expected, but multiple objects are returned.

**HTTPError**
 *tachyon.HTTPError*

 The base class for HTTP exceptions.

**HTTPBadRequest**
 *tachyon.HTTPBadRequest*

 400 Bad Request. The server cannot or will not process the request due to something that is perceived to be a client error.

**HTTPUnauthorized**
 *tachyon.HTTPUnauthorized*

 401 Unauthorized. The request has not been applied because it lacks valid authentication credentials for the target resource.

**HTTPForbidden**
 *tachyon.HTTPForbidden*

 403 Forbidden. The server understood the request but refuses to authorize it.

**HTTPNotFound**
 *tachyon.HTTPNotFound*

 404 Not Found. The origin server did not find a current representation for the target resource or is not willing to disclose that one exists.

**HTTPMethodNotAllowed**
 *tachyon.HTTPMethodNotAllowed*

 405 Method Not Allowed. The method received in the request-line is known by the origin server but not supported by the target resource.

**HTTPNotAcceptable**
 *tachyon.HTTPNotAcceptable*

 406 Not Acceptable. The target resource does not have a current representation that would be acceptable to the user agent, according to the proactive negotiation header fields received in the request, and the server is unwilling to supply a default representation.

**HTTPConflict**
 *tachyon.HTTPConflict*

 409 Conflict. The request could not be completed due to a conflict with the current state of the target resource. This code is used in situations where the user might be able to resolve the conflict and resubmit the request.

**HTTPLengthRequired**
 *tachyon.HTTPLengthRequired*

 411 Length Required. The server refuses to accept the request without a defined Content-Length.

**HTTPPreconditionFailed**
 *tachyon.HTTPPreconditionFailed*

 412 Precondition Failed. One or more conditions given in the request header fields evaluated to false when tested on the server.

**HTTPUnsupportedMediaType**
 *tachyon.HTTPUnsupportedMediaType*

 415 Unsupported Media Type. The origin server is refusing to service the request because the payload is in a format not supported by this method on the target resource.

**HTTPUnprocessableEntity**
 *tachyon.HTTPUnprocessableEntity*

 422 Unprocessable Entity. The server understands the content type of the request entity (hence a 415 Unsupported Media Type status code is inappropriate), and the syntax of the request entity is correct (thus a 400 Bad Request status code is inappropriate) but was unable to process the contained instructions.

**HTTPTooManyRequests**
 *tachyon.HTTPTooManyRequests*

 429 Too Many Requests. The user has sent too many requests in a given amount of time (“rate limiting”).

**HTTPUnavailableForLegalReasons**
 *tachyon.HTTPUnavailableForLegalReasons*

 The server is denying access to the resource as a consequence of a legal demand.

**HTTPInternalServerError**
 *tachyon.HTTPInternalServerError*

 500 Internal Server Error. The server encountered an unexpected condition that prevented it from fulfilling the request.

**HTTPBadGateway**
 *tachyon.HTTPBadGateway*

 502 Bad Gateway. The server, while acting as a gateway or proxy, received an invalid response from an inbound server it accessed while attempting to fulfill the request.

**HTTPInvalidHeader**
 *tachyon.HTTPInvalidHeader*

 400 Bad Request. One of the headers in the request is invalid.

**HTTPMissingHeader**
 *tachyon.HTTPMissingHeader*

 400 Bad Request. A header is missing from the request.

**HTTPInvalidParam**
 *tachyon.HTTPInvalidParam*

 400 Bad Request. A parameter in the request is invalid. This error may refer to a parameter in a query string, form, or document that was submitted with the request.

**HTTPMissingParam**
 *tachyon.HTTPMissingParam*

 400 Bad Request. A parameter is missing from the request. This error may refer to a parameter in a query string, form, or document that was submitted with the request.


Custom HTTP Errors
------------------

You can create custom HTTP errors by creating templates after the status code. For example 404.html. These will automatically be used.

