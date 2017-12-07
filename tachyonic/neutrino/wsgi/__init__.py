# -*- coding: utf-8 -*-
from .wsgi import Wsgi

# Launch WSGI Application
app = Wsgi()

# For Conveniance.
# References to Wsgi methods.
router = app.router
jinja = app.jinja
app.get_template
app.render_template
