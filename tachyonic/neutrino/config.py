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
    def __init__(self):
        self.data = {}

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        if key in self.data:
            return self.get(key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        try:
            del self.data[key]
        except KeyError:
            pass

    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def get(self, key, default=None):
        try:
            return self.data[key]
        except KeyError:
            return default

    def getboolean(self, key=None, default=False):
        if key in self.data:
            if self.data[key] == 'True' or self.data[key] == 'true':
                return True
            else:
                return False
        else:
            return default

    def getitems(self, key=None):
        if key in self.data:
            conf = self.data[key].replace(' ', '')
            if conf == '':
                return []
            else:
                return conf.split(',')
        else:
            return []


class Config(object):
    configs = {}

    def __init__(self, config_file):
        self.config = {}
        if os.path.isfile(config_file):
            if config_file not in self.configs:
                config = configparser.ConfigParser()
                config.read(config_file)
                sections = config.sections()

                for section in sections:
                    self.config[section] = Section()
                    options = config.options(section)
                    for option in options:
                        self.config[section][option] = config.get(section, option)
                self.configs[config_file] = self.config
            else:
                self.config = self.configs[config_file]
        else:
            raise tachyonic.neutrino.Error('Configuration file not found: %s' % config_file)

    def get(self, key=None):
        if key in self.config:
            return self.config[key]
        else:
            return Section()

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

    def __iter__(self):
        return iter(self.config)

    def __len__(self):
        return len(self.config)
