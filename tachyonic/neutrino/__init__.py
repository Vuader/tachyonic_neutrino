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
root.app = app
root.router = app.router
root.jinja = app.jinja
root.render_template = app.render_template

