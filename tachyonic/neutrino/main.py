#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""

from __future__ import print_function

import os
import sys
import site
import re
import argparse
import logging
import time
import datetime
import hashlib
from wsgiref import simple_server

from pkg_resources import resource_stream, resource_listdir, resource_isdir, resource_exists

from tachyonic.neutrino import app
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.utils.general import import_module
from tachyonic.neutrino.config import Config
from tachyonic.neutrino import metadata

log = logging.getLogger(__name__)

def _create_dir(path, new):
    new = os.path.normpath('%s%s' % (path, new))
    if not os.path.exists(new):
        os.makedirs(new)
        print('Created directory: %s' % new)


def _copy_resource(path, src, dst=''):
    dst = os.path.normpath('%s/%s/%s' % (path, dst, src))
    src_file = resource_stream('tachyonic.neutrino', 'resources/%s' % (src)).read()
    if not os.path.exists(dst):
        with open(dst, 'wb') as handle:
            handle.write(src_file)
            print('Created %s' % dst)


def _copy_file(module, path, src, dst, update=True):
    try:
        import_module(module)
    except ImportError:
        print("Neutrino python package not found %s" % module)
        exit()

    dst = os.path.normpath("%s/%s" % (path, dst))
    if resource_exists(module, src):
        src_file = resource_stream(module, src).read()
        if not os.path.exists(dst):
            with open(dst, 'wb') as handle:
                handle.write(src_file)
                print("Created %s" % dst)
        else:
            if update is False:
                dst = "%s.default" % (dst,)
                with open(dst, 'wb') as handle:
                    handle.write(src_file)
                    print("Updated %s" % dst)
            else:
                src_sig = hashlib.md5(src_file)
                dst_file = open(dst, 'rb').read()
                dst_sig = hashlib.md5(dst_file)
                if src_sig.hexdigest() != dst_sig.hexdigest():
                    with open(dst, 'wb') as handle:
                        handle.write(src_file)
                        print("Updated %s" % dst)


def _empty_file(path, src, dst=''):
    dst = os.path.normpath("%s/%s/%s" % (path, dst, src))
    if not os.path.exists("%s" % (dst,)):
        with open(dst, 'wb') as handle:
            handle.write('')
            print("Created %s" % dst)


def static(args):
    path = os.path.abspath(args.path)
    app_root = path
    os.chdir(app_root)
    sys.path.append(app_root)
    site.addsitedir(app_root)


    def _walk(local, module, path):
        for filename in resource_listdir(module, path):
            fullname = path + '/' + filename
            if resource_isdir(module, fullname):
                _create_dir(local, '/%s' % fullname)
                _walk(local, module, fullname)
            else:
                _copy_file(module, local, fullname, fullname)

    if args.s is not None:
        modules = [ args.s ]
    else:
        config = Config('%s/settings.cfg' % path)
        app_config = config.get('application')
        modules = app_config.getitems('modules')

    if os.path.exists('%s/settings.cfg' % path):
        for module in modules:
            if resource_exists(module, 'static'):
                _create_dir('', '%s/static' % path)
                _walk(path, module, 'static')
    else:
        print("Missing settings.cfg - check path specified")
        exit()


def setup(args):
    path = os.path.abspath(args.path)
    module = args.s
    if module == 'tachyonic.neutrino':
        print("Your suppose to install tachyonic.neutrino modules not neutrino itself")
        exit()
    _copy_file(module, path, 'resources/settings.cfg', 'settings.cfg', False)
    _copy_file(module, path, 'resources/policy.json', 'policy.json', False)
    _create_dir(path, '/wsgi')
    _copy_resource(path, '/wsgi/app.wsgi')
    _create_dir(path, '/templates')
    static(args)
    _create_dir(path, '/tmp')
    print("\nPlease ensure %s/tmp and sub-directories is writeable by Web Server User\n" %path)


def server(args):
    try:
        from gunicorn.app.base import Application
    except:
        print("Requires Gunicorn - pip install gunicorn")
        exit()

    from gunicorn import util
    import multiprocessing
    import gunicorn.app.base
    from gunicorn.six import iteritems

    def number_of_workers():
        return (multiprocessing.cpu_count() * 2) + 1

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super(StandaloneApplication, self).__init__()

        def load_config(self):
            config = dict([(key, value) for key, value in iteritems(self.options)
                           if key in self.cfg.settings and value is not None])
            for key, value in iteritems(config):
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application


    path = args.path

    app_root = path
    if os.path.exists("%s/settings.cfg" % (path,)):
        config = Config("%s/settings.cfg" % (path,))
        app_config = config.get('application')
        static_path = app_config.get('static', '/static')
    else:
        print("Missing settings.cfg - check path specified")
        exit()


    def serve_static(req, resp):
        sfile = open(req.get_path().strip('/'), 'rb').read()
        sname = req.get_path().strip('/')
        ssplit = sname.split('.')
        sext = ssplit[len(ssplit)-1].lower()

        try:
            if "css" in sext:
                resp.headers['Content-Type'] = const.TEXT_CSS
            elif "txt" in sext:
                resp.headers['Content-Type'] = const.TEXT_PLAIN
            elif "html" in sext:
                resp.headers['Content-Type'] = const.TEXT_HTML
            elif "htm" in sext:
                resp.headers['Content-Type'] = const.TEXT_HTML
            elif "jpeg" in sext:
                resp.headers['Content-Type'] = const.IMAGE_JPEG
            elif "jpg" in sext:
                resp.headers['Content-Type'] = const.IMAGE_JPEG
            elif "gif" in sext:
                resp.headers['Content-Type'] = const.IMAGE_GIF
            elif "png" in sext:
                resp.headers['Content-Type'] = const.IMAGE_PNG
            else:
                resp.headers['Content-Type'] = const.APPLICATION_OCTET_STREAM

            return [ sfile ]
        except Exception as e:
            return "Error %s" % (e,)

    path = os.path.abspath(args.path)
    print('Loading Application %s' % path)
    ip = args.i
    port = args.p

    os.chdir(app_root)
    sys.path.append(app_root)
    site.addsitedir(app_root)

    options = {
        'bind': '%s:%s' % (ip, port),
        'workers': number_of_workers(),
    }
    app_wsgi = app(app_root)
    app.router.add(const.HTTP_GET, static_path + '/*', serve_static)
    StandaloneApplication(app_wsgi, options).run()


def create(args):
    path = args.path
    if os.path.exists(path):
        _copy_resource(path, '/settings.cfg')
        _create_dir(path, '/wsgi')
        _copy_resource(path, '/wsgi/app.wsgi')
        _create_dir(path, '/templates')
        _create_dir(path, '/static')
        _create_dir(path, '/myproject')
        _copy_resource(path, '/myproject/__init__.py')
        _copy_resource(path, '/myproject/views.py')
        _copy_resource(path, '/myproject/model.py')
        _copy_resource(path, '/myproject/middleware.py')
        _empty_file(path, '/myproject/model.py')
        _create_dir(path, '/myproject/static')
        _create_dir(path, '/myproject/static/myproject')
        _create_dir(path, '/myproject/templates')
        _create_dir(path, '/tmp')
        _create_dir(path, '/tmp/.cache')
        _create_dir(path, '/tmp/.cache/Python-Eggs')
        print("\nPlease ensure %s/tmp and sub-directories is writeable by Web Server User\n" % path)
    else:
        print("Invalid path")


def session(args):
    path = args.path
    c = 0
    if os.path.exists("%s/settings.cfg" % (path,)):
        config = Config("%s/settings.cfg" % (path,))
        app_config = config.get('application')
        session_expire = app_config.get('session_expire', 3600)
        r = re.compile('^.*session$')
        if os.path.exists("%s/tmp" % (path,)):
            files = os.listdir("%s/tmp" % (path,))
            for f in files:
                fpath = "%s/tmp/%s" % (path, f)
                if os.path.isfile(fpath):
                    if r.match(fpath):
                        now = datetime.datetime.now()
                        ts = int(time.mktime(now.timetuple()))
                        stat = os.stat(fpath)
                        lm = int(stat.st_mtime)
                        if ts - lm > session_expire:
                            os.remove(fpath)
                            c += 1
            print("Removed expired sessions: %s\n" % c)
        else:
            print("Missing tmp folder")
    else:
        print("Missing settings.cfg or invalid path")


def main(argv):
    description = metadata.description + ' ' + metadata.version
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('path', help='Application root path')
    group.add_argument('-c', help='Create new application root structure', dest='funcs', const=create, action='append_const')
    group.add_argument('-e', help='Wipe expired sessions', dest='funcs', const=session, action='append_const')
    group.add_argument('-s', help='Re-Initilize/Setup Application')
    group.add_argument('-g', help='Collect and Populate /static as per settings.cfg modules', dest='funcs', const=static, action='append_const')
    group.add_argument('-t', help='Start builtin server (only for testing)', dest='funcs', const=server, action='append_const')
    parser.add_argument('-i', help='Binding IP Address (127.0.0.1)', default='127.0.0.1')
    parser.add_argument('-p', help='Binding Port (8080)', default='8080')
    args = parser.parse_args()
    if 'path' in args:
        args.path = os.path.abspath(args.path)
        if not os.path.exists(args.path):
            print("Application Path invalid %s" % (args.path))
            exit()
    if args.funcs is not None:
        print("%s\n" % description)
        for f in args.funcs:
            f(args)
    if args.funcs is None or len(args.funcs) == 0:
        if args.s is not None:
            print("%s\n" % description)
            setup(args)
        else:
            parser.print_help()
    return 0


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    entry_point()
