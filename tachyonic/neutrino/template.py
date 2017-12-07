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

import os
import logging
import traceback

from pkg_resources import DefaultProvider, ResourceManager, get_provider
from jinja2 import Environment
from jinja2.exceptions import TemplateNotFound
from jinja2.loaders import BaseLoader
from jinja2 import loaders

from tachyonic.neutrino.threaddict import ThreadDict

log = logging.getLogger(__name__)

class GetTemplateWrapper(object):
    """Wrapper for Jinja2 loaded template.
    """
    def __init__(self, template, request):
        self._request = request
        self._template = template

    def render(self, **kwargs):
        """Renders this template with a given kwargs as context.

        If kwargs isn’t provided, the engine will render the template with an
        empty context.
        """
        for r in self._request:
            kwargs[r] = self._request[r]
        return self._template.render(**kwargs)


class Jinja(object):
    """Neutrino being a web framework, we need a convenient way to generate
    HTML dynamically. The most common approach relies on templates. A template
    contains the static parts of the desired HTML output as well as some
    special syntax describing how dynamic content will be inserted.
    """
    def __init__(self):
        self._request = ThreadDict()
        self._loader = JinjaLoader()
        self._jinja = Environment(loader=self._loader)

    def clean_up(self):
        """Clear global context related to request.
        """
        self._request.clear()

    def get_template(self, *args, **kwargs):
        """This method loads the template with the given name and returns a
        GetTemplateWrapper object.
        """
        t = self._jinja.get_template(*args, **kwargs)
        w = GetTemplateWrapper(t, self._request)
        return w

    def render_template(self, template, **kwargs):
        """Renders this template with a given kwargs as context.

        If kwargs isn’t provided, the engine will render the template with an
        empty context.

        Conveniance method so no need to use get_template() method and use
        render() method on Template Object.
        """
        t = self.get_template(template)
        return t.render(**kwargs)

    def __getattr__(self, attr):
        if attr == 'request':
            return self._request
        elif attr == 'load_templates':
            return self._loader.load_templates
        elif attr == 'globals':
            return getattr(self._jinja, attr)
        elif attr == 'list_templates':
            return getattr(self._jinja, attr)
        else:
            raise Exception("Neutrino Jinja Environment has no attribute %s" % (attr,))


class JinjaLoader(BaseLoader):
    """Jinja class for loading templates.
    """
    def load_templates(self, modules, override_path):
        """Load Templates Jinja2 Templates

        Initialize loading for Jinja2 Templates.

        Please note: Can only be performed after modules import.
            * If done before you get poorly handled error messages.
            * Because jinja also trieds to import above moodules.
            * When import fails at this point error is handled differently.

        Args:
            modules (list): List of python packages that could contain
                templates for use.
            override_path (str): Path locating overriding templates.
        """
        self.searchpath = "%s/templates" % (override_path,)
        try:
            self.fsl = loaders.FileSystemLoader(self.searchpath)
        except Exception as e:
            log.error(e)

        self.modules = modules
        self.packages = {}
        self.encoding = 'utf-8'
        self.package_path = "templates"
        self.manager = ResourceManager()
        for package_name in self.modules:
            try:
                pkg = self.packages[package_name] = {}
                pkg['provider'] = get_provider(package_name)
                pkg['fs_bound'] = isinstance(pkg['provider'], DefaultProvider)
            except Exception as e:
                trace = str(traceback.format_exc())
                log.error("Can't import module %s\n%s" % (str(e), trace))

    def get_source(self, environment, template):
        """Get raw template for environment.

        First attempts to load overriding template then uses template within
        specified package. For example "package/template.html"
        """
        pieces = loaders.split_template_path(template)
        try:
            return self.fsl.get_source(environment, template)
        except Exception:
            pass

        if len(pieces) > 1 and pieces[0] in self.packages:
            pkg_name = pieces[0]
            pkg = self.packages[pkg_name]
            del pieces[0]
            p = '/'.join((self.package_path,) + tuple(pieces))
            if not pkg['provider'].has_resource(p):
                raise TemplateNotFound(template)
        else:
            raise TemplateNotFound(template)

        filename = uptodate = None
        if pkg['fs_bound']:
            filename = pkg['provider'].get_resource_filename(self.manager, p)
            mtime = os.path.getmtime(filename)

            def uptodate():
                try:
                    return os.path.getmtime(filename) == mtime
                except OSError:
                    return False

        source = pkg['provider'].get_resource_string(self.manager, p)
        return source.decode(self.encoding), filename, uptodate

    def list_overrides(self):
        """Returns a list of overiding templates for this environment.

        Overiding templates are located within wsgi application installation
        path in templates.

        Templates to override are located in package/templates path structure.
        For example /var/www/ui/templates/template.html
        """
        fsl = self.fsl.list_templates()
        return fsl

    def list_templates(self):
        """Returns a list of templates for this environment.

        Templates are located within the python package source.
        """
        path = self.package_path
        if path[:2] == './':
            path = path[2:]
        elif path == '.':
            path = ''
        offset = len(path)
        results = []

        def _walk(path, pkg):
            for filename in pkg['provider'].resource_listdir(path):
                fullname = path + '/' + filename
                if pkg['provider'].resource_isdir(fullname):
                    _walk(fullname, pkg)
                else:
                    p = fullname[offset:].lstrip('/')
                    p = "%s/%s" % (package_name, p)
                    results.append(p)

        for package_name in self.packages:
            pkg = self.packages[package_name]
            if pkg['provider'].resource_isdir(path):
                _walk(path, pkg)
        results.sort()

        return results
