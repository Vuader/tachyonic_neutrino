from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import logging
import traceback

from pkg_resources import DefaultProvider, ResourceManager, get_provider
from jinja2 import Environment
from jinja2.exceptions import TemplateNotFound
from jinja2.loaders import BaseLoader
from jinja2 import loaders
import threading

from tachyonic.neutrino.utils.threaddict import ThreadDict

log = logging.getLogger(__name__)

lock = threading.Lock()


class GetTemplateWrapper(object):
    def __init__(self, template, request):
        self._request = request
        self._template = template

    def render(self, **kwargs):
        for r in self._request:
            kwargs[r] = self._request[r]
        return self._template.render(**kwargs)


class Jinja(object):
    def __init__(self):
        self._request = ThreadDict()
        self._loader = JinjaLoader()
        self._jinja = Environment(loader=self._loader)

    def clean_up(self):
        self._request.clear()

    def get_template(self, *args, **kwargs):
        t = self._jinja.get_template(*args, **kwargs)
        w = GetTemplateWrapper(t, self._request)
        return w

    def render_template(self, template, **kwargs):
        t = self.get_template(template)
        return t.render(**kwargs)

    def __getattr__(self, attr):
        lock.acquire()
        try:
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
        finally:
            lock.release()


class JinjaLoader(BaseLoader):
    def load_templates(self, config, root_path):
        self.searchpath = "%s/templates" % (root_path,)
        try:
            self.fsl = loaders.FileSystemLoader(self.searchpath)
        except Exception as e:
            log.error(e)

        self.config = config
        self.app_config = self.config.get('application')
        self.modules = self.app_config.getitems('modules')
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

    def list_templates(self):
        fsl = []
        try:
            # fsl = self.fsl.get_source(environment, template)
            pass
        except Exception as e:
            log.error(e)

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

        return results + fsl
