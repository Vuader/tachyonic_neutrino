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

from __future__ import print_function

import os
import sys
import site
import logging
import mimetypes
from multiprocessing import Process

from tachyonic.common import constants as const

from tachyonic.neutrino import app
from tachyonic.neutrino.config import Config

log = logging.getLogger(__name__)


def server(app_root, ip='127.0.0.1', port='8080'):
    try:
        from gunicorn.app.base import Application
    except:
        print("Requires Gunicorn - pip install gunicorn")
        exit()

    from gunicorn import util
    import multiprocessing
    import gunicorn.app.base
    from gunicorn.six import iteritems

    app_root = os.path.abspath(app_root)

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


    if not os.path.exists("%s/settings.cfg" % (app_root,)):
        print("Missing settings.cfg - check path specified")
        exit()

    def serve_static(req, resp):
        sfile = open(req.get_path().strip('/'), 'rb').read()

        try:
            resp.headers['Content-Type'], encoding = mimetypes.guess_type(req.get_path())
            if resp.headers['Content-Type'] is None:
                resp.headers['Content-Type'] = const.APPLICATION_OCTET_STREAM

            return [ sfile ]
        except Exception as e:
            return "Error %s" % (e,)

    print('Loading Application %s' % app_root)

    os.chdir(app_root)
    sys.path.append(app_root)
    site.addsitedir(app_root)

    options = {
        'bind': '%s:%s' % (ip, port),
        'workers': number_of_workers(),
        'capture_output': True
    }

    app_wsgi = app(app_root)
    static_path = app.config.get('application').get('static','/static')
    app.router.add(const.HTTP_GET, static_path + '/*', serve_static)
    while True:
        StandaloneApplication(app_wsgi, options).run()


def auto_restart(app_root, ip='127.0.0.1', port='8080'):
    try:
        while True:
            p = Process(target=server, args=(app_root, ip, port))
            p.start()
            p.join()
    except KeyboardInterrupt:
            print("Shutting Down Webserver")

