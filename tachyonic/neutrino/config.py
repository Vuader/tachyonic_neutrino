from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import logging

import tachyonic.neutrino

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
        if key in self.options:
            return self.config.get(self.section, key)
        else:
            raise KeyError(key)

    def __iter__(self):
        return iter(self.config.items(self.section))

    def __repr__(self):
        return repr(self.section)

    def __str__(self):
        return str(self.section)

    def get(self, key, default=None):
        if key in self.options:
            return self.config.get(self.section, key)
        else:
            return default

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
            conf = self.get(key)
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
    def __init__(self, config_file):
        self.config = {}
        self.sections = {}
        if os.path.isfile(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)
            sections = config.sections()
            for section in sections:
                self.sections[section] = Section(section, config)
            self.config = config
        else:
            raise tachyonic.neutrino.Error('Configuration file not found: %s' % config_file)

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
