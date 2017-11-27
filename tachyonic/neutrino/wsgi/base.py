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
import sys
import logging
import json
import traceback
import signal

from jinja2.exceptions import TemplateNotFound

from tachyonic.neutrino import exceptions
from tachyonic.neutrino import constants as const
from tachyonic.neutrino.imports import import_modules, init_classes
from tachyonic.neutrino.strings import if_unicode_to_utf8
from tachyonic.neutrino.dt import Datetime
from tachyonic.neutrino.wsgi import restart
from tachyonic.neutrino.wsgi import template
from tachyonic.neutrino.config import Config
from tachyonic.neutrino.logger import Logger
from tachyonic.neutrino.wsgi.router import Router
from tachyonic.neutrino.wsgi.request import Request
from tachyonic.neutrino.wsgi.response import Response
from tachyonic.neutrino.mysql import Mysql
from tachyonic.neutrino.redissy import redis
from tachyonic.neutrino.web.dom import Dom
from tachyonic.neutrino.policy import Policy
from tachyonic.neutrino.shrek import Shrek

log = logging.getLogger(__name__)


class Base(object):
    def __init__(self):
        self.app_root = os.getcwd()
        self.router = Router()
        self.jinja = template.Jinja()
        self.get_template = self.jinja.get_template
        self.render_template = self.jinja.render_template
        self.debug = True
        self.context = {}
        self.policy = {}
        self.config = Config()
        self.logger = Logger()
        self._cleanup_funcs = []

    def __call__(self, app_root):
        """Initialize WSGI Application.

        Load settings.cfg, policies, logging and modules.

        Args:
            app_root (string): Root path for application where settings.cfg,
                overriding templates, static files and application tmp is located.

        Returns:
            method: (self.interface) method callable from WSGI server.
        """
        try:
            # Some default Attributes
            self.app_root = app_root.rstrip('/')

            # Ensure in application root
            os.chdir(self.app_root)

            # Prepend app_root to system path for python
            # imports during development
            sys.path.insert(0, self.app_root)

            # Load Configuration
            config_file_path = "%s/settings.cfg" % (self.app_root,)
            self.config.load(config_file_path)
            self.app_config = self.config.get('application')
            self.log_config = self.config.get('logging')
            self.debug = self.log_config.get_boolean('debug')
            self.app_name = self.app_config.get('name','tachyonic')

            # Load Logger
            log_config = self.config.get('logging')
            self.logger.load(app_name=self.app_name,
                             syslog_host=log_config.get('host', None),
                             syslog_port=log_config.get('port', 514),
                             debug=self.debug,
                             log_file=log_config.get('file', None))

            log.info("STARTING APPLICATION PROCESS FOR %s" % (self.app_name,))

            # Load Policy if exists
            policy_file_path = "%s/policy.json" % (self.app_root,)
            if os.path.isfile(policy_file_path):
                policy_file = open(policy_file_path, 'r')
                self.policy = json.loads(policy_file.read())
                policy_file.close()

            # Monitor Python modules and configs for changes.
            # If change detected kill myself... only while debug is enabled.
            # This makes it easier to do development...
            if self.debug is True:
                restart.start(interval=1.0)
                restart.track(config_file_path)
                restart.track(policy_file_path)

            # Load/Import modules
            self.app_config.get_items('modules')
            modules = self.app_config.get_items('modules')
            self.modules = import_modules(modules)

            # Load Jinja Templates - Can only be performed after module import.
            # If done before you get poorly handled error messages.
            # Because jinja also trieds to import above moodules.
            self.jinja.load_templates(modules, "%s/templates" % app_root)

            # Load Middleware - at this point modules should
            # already be imported.
            middleware = self.app_config.get_items('middleware')
            self.middleware = init_classes(middleware)

            # Return WSGI Callable Interface
            return self.interface

        except Exception as e:
            trace = str(traceback.format_exc())
            log.error("%s\n%s" % (e, trace))
            log.error("RESTARTING (pid=%d)" % os.getpid())

            try:
                self._cleanup()
            except:
                pass

            if self.debug is True:
                os.kill(os.getpid(), signal.SIGINT)

    def register_cleanup(self, function):
        """Register cleanup function run at end of request.

        Args:
            function (function): Any callable to run at end of request.
        """
        if function not in self._cleanup_funcs:
            self._cleanup_funcs.append(function)

    def _cleanup(self):
        for func in self._cleanup_funcs:
            func()

        Shrek.close()
        self.jinja.clean_up()
        self.logger.stdout.flush()
        sys.stdout.flush()
        sys.stderr.flush()

    def resources(self):
        def resource_wrapper(f):
            f()

        return resource_wrapper

    def resource(self, method, resource, policy=None):
        def resource_wrapper(f):
            return self.router.add(method, resource, f, policy)

        return resource_wrapper
