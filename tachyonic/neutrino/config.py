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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import logging

from tachyonic.common import exceptions

log = logging.getLogger(__name__)


class Section(object):
    def __init__(self, section=None, config=None):
        if config is not None:
            self.config = config
        else:
            self.config = None
        if section is not None:
            self.section = section
            self.options = config.options(section)
        else:
            self.section = None
            self.options = []

    def __getitem__(self, key):
        if key in self.options and self.config.get(self.section, key).strip() != '':
            return self.config.get(self.section, key)
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        return self.config.set(self.section, key, value)

    def __contains__(self, key):
        if key in self.options:
            if self.config.get(self.section, key).strip() != '':
                return True
            else:
                return False
        else:
            return False

    def __iter__(self):
        return iter(self.config.items(self.section))

    def __repr__(self):
        return repr(self.section)

    def __str__(self):
        return str(self.section)

    def get(self, key, default=None):
        if key in self.options:
            val = self.config.get(self.section, key)
            if val.strip() != '':
                return val
            else:
                return default
        else:
            return default

    def set(self, key, value):
        return self.config.set(self.section, key, value)

    def dict(self):
        d = {}
        for key in self.options:
            d[key] = self.config.get(self.section, key)
        return d

    def getboolean(self, key=None, default=False):
        if key in self.options:
            return self.config.getboolean(self.section, key)
        else:
            return default

    def getitems(self, key):
        if key in self.options:
            conf = self.get(key, '')
            conf = conf.replace(' ', '')
            if conf == '':
                return []
            else:
                return conf.split(',')
        else:
            return []

    def items(self, key):
        return self.getitems(self, key)


class Config(object):
    def __init__(self, config_file=None):
        self.sections = {}
        self.config = configparser.ConfigParser()
        if config_file is not None:
            self.load(config_file)

    def load(self, config_file):
        if os.path.isfile(config_file) and os.access(config_file, os.R_OK):
            self.config.read(config_file)
            sections = self.config.sections()
            for section in sections:
                self.sections[section] = Section(section, self.config)
        elif not os.path.isfile(config_file):
            raise exceptions.Error('Configuration file not found: %s' % config_file)
        elif not os.access(config_file, os.R_OK):
            raise exceptions.Error('Configuration permission denied: %s' % config_file)
        else:
            raise exceptions.Error('Configuration error loading file: %s' % config_file)


    def save(self, config_file):
        with open(config_file, 'wb') as f:
            self.config.write(f)

    def get(self, key):
        if key in self.sections:
            return self.sections[key]
        else:
            return Section()

    def __getitem__(self, key):
        return self.sections[key]

    def __contains__(self, key):
        if key in self.sections:
            return True
        else:
            return False

    def getitems(self, key):
        if key in self.sections:
            return self.config.items(key)
        else:
            return []

    def items(self, key):
        return self.getitems(self, key)
