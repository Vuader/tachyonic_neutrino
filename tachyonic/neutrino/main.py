#!/usr/bin/env python
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

"""Program entry point"""

import os
import sys
import site
import re
import argparse
import logging
import time
import datetime
import hashlib

from pkg_resources import resource_stream, resource_listdir, resource_isdir, resource_exists

import tachyonic.neutrino
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.imports import import_module
from tachyonic.neutrino import app
from tachyonic.neutrino.server import auto_restart
from tachyonic.neutrino.config import Config
from tachyonic.neutrino import metadata

log = logging.getLogger(__name__)

def _create_dir(path, new):
    new = os.path.normpath('%s%s' % (path, new))
    if not os.path.exists(new):
        os.makedirs(new)
        print('Created directory: %s' % new)


def _copy_file(module, path, src, dst, update=True):
    try:
        import_module(module)
    except ImportError as e:
        print("Import Error %s\n%s" % (module, e))
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
                if not os.path.exists(dst):
                    with open(dst, 'wb') as handle:
                        handle.write(src_file)
                        print("Created %s" % dst)
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


def _recursive_copy(local, module, path):
    for filename in resource_listdir(module, path):
        fullname = path + '/' + filename
        if resource_isdir(module, fullname):
            _create_dir(local, '/%s' % filename)
            _recursive_copy("%s/%s" % (local, filename), module, fullname)
        else:
            _copy_file(module, local, fullname, filename)


def _static(args):
    path = os.path.abspath(args.path)
    app_root = path
    os.chdir(app_root)
    sys.path.append(app_root)
    site.addsitedir(app_root)

    if args.module is not None:
        modules = [ args.module ]
    else:
        config = Config('%s/settings.cfg' % path)
        app_config = config.get('application')
        modules = app_config.getitems('modules')

    if os.path.exists('%s/settings.cfg' % path):
        for module in modules:
            if resource_exists(module, 'static'):
                _create_dir('', '%s/static' % path)
                _recursive_copy("%s/static" % path, module, 'static')
    else:
        print("Missing settings.cfg - check path specified")
        exit()


def _setup(args):
    path = os.path.abspath(args.path)
    module = args.module

    if module == 'tachyonic.neutrino':
        print("Your suppose to install tachyonic.neutrino modules not neutrino itself")
        exit()

    if os.path.isfile("%s/settings.cfg" % path):
        config = Config()
        config.load("%s/settings.cfg" % path)
        m = config.get('application').get('modules').replace(' ','').split(',')
        if module not in m:
            m.append(module)
        m = "%s" % ", ".join(m)
        config.get('application').set('modules', m)
        config.save("%s/settings.cfg" % path)
        _copy_file(module, path, 'resources/settings.cfg',
                   '%s_settings.cfg.default' % module,
                   True)
    else:
        _copy_file(module, path, 'resources/settings.cfg', 'settings.cfg', False)


    if os.path.isfile("%s/policy.json" % path):
        _copy_file(module, path, 'resources/policy.json',
                   '%s_policy.json.default' % module,
                   True)
    else:
        _copy_file(module, path, 'resources/policy.json', 'policy.json', True)

    _create_dir(path, '/wsgi')
    _copy_file('tachyonic.neutrino', path, 'resources/wsgi/app.py', 'wsgi/app.py', False)
    _copy_file('tachyonic.neutrino', path, 'resources/wsgi/__init__.py', 'wsgi/__init__.py')
    _create_dir(path, '/templates')
    _static(args)
    _create_dir(path, '/tmp')
    print("\nPlease ensure %s/tmp and sub-directories is writeable by Web Server User\n" %path)


def _server(args):
    auto_restart(args.path, args.ip, args.port)


def _create(args):
    path = os.path.abspath(args.path)
    name = args.name
    config = Config()
    if os.path.exists(path):
        if os.path.isfile("%s/settings.cfg" % path):
            config.load("%s/settings.cfg" % path)
            _copy_file('tachyonic.neutrino',
                       path,
                       'resources/settings.cfg',
                       'neutrino_settings.cfg.default')
        else:
            _copy_file('tachyonic.neutrino',
                       path,
                       'resources/settings.cfg',
                       'settings.cfg')
            config.load("%s/settings.cfg" % path)
            config.get('application').set('name', name.replace('.',' ').upper())

        m = config.get('application').get('modules','').replace(' ','').split(',')
        if name not in m:
            if m[0] == "":
                m[0] = name
            else:
                m.append(name)
        m = ", ".join(m)
        config.get('application').set('modules', m)
        config.save("%s/settings.cfg" % path)

        _create_dir(path, '/wsgi')
        _copy_file('tachyonic.neutrino',
                   path,
                   'resources/wsgi/app.py',
                   'wsgi/app.py')
        _copy_file('tachyonic.neutrino',
                   path,
                   'resources/wsgi/__init__.py',
                   'wsgi/__init__.py')

        _create_dir(path, '/templates')
        _create_dir(path, '/static')
        _create_dir(path, '/tmp')
        _create_dir(path, '/tmp/Python-Eggs')

        package = "/%s" % name.replace('.', '/')
        _create_dir(path, package)

        _recursive_copy("%s/%s" % (path, package),
                        'tachyonic.neutrino',
                        'resources/myproject')

        _create_dir(path, '/%s/static/%s' % (package, name))

        print("\nPlease ensure %s/tmp and sub-directories is writeable by Web Server User\n" % path)
    else:
        print("Invalid path")


def _session(args):
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

    parser.add_argument('path',
                        help='Application root path')

    group.add_argument('-c',
                       dest='name',
                       help='Create new application root structure')

    group.add_argument('-e',
                       help='Wipe expired sessions',
                       dest='funcs',
                       const=_session,
                       action='append_const')

    group.add_argument('-s',
                       dest='module',
                       help='Re-Initilize/Setup Application')

    group.add_argument('-g',
                       help='Collect and Populate /static as per' +
                       'settings.cfg modules',
                       dest='funcs',
                       const=_static,
                       action='append_const')

    group.add_argument('-t',
                       help='Start builtin server (only for testing)',
                       dest='funcs',
                       const=_server,
                       action='append_const')

    parser.add_argument('--ip',
                        help='Binding IP Address (127.0.0.1)',
                        default='127.0.0.1')

    parser.add_argument('--port',
                        help='Binding Port (8080)',
                        default='8080')

    args = parser.parse_args()

    if 'path' in args:
        args.path = os.path.abspath(args.path)
        if not os.path.exists(args.path):
            print("Application Path invalid %s" % (args.path))
            exit()
    else:
        print("Application Path required" % (args.path))
        exit()

    if args.funcs is not None:
        print("%s\n" % description)
        for f in args.funcs:
            f(args)

    if args.funcs is None or len(args.funcs) == 0:
        if args.module is not None:
            print("%s\n" % description)
            _setup(args)
        elif args.name is not None:
            _create(args)
        else:
            parser.print_help()

    return 0


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    entry_point()
