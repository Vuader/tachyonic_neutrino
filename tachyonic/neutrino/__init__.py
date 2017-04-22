# -*- coding: utf-8 -*-
from __future__ import absolute_import

import tachyonic as root
from .wsgi import Wsgi

from . import metadata

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

_cc = 0

def creation_counter():
    global _cc
    _cc += 1
    return _cc


app = Wsgi()


# BACKWARDS COMPATIBLE - Tachyonic namespace
# These only work if Neutrino is imported.
# DEPRECATED: This will be removed when possible in future!!!
root.app = app
root.router = app.router
root.jinja = app.jinja
root.get_template = app.get_template
root.render_template = app.render_template

# Global debug used to enhance performance.
# Prevent modules code from logging. Even if its filtered by the logging
# facilities this does improve resource usage.
root.debug = app.debug
