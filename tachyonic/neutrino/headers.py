from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from tachyonic.neutrino.utils.general import is_byte_string
log = logging.getLogger(__name__)


class Headers(object):
    def __init__(self,request=True):
        self.data = {}
        self.request = request

    def __setitem__(self, key, value):
        key = str(key).lower()
        if self.request is True:
            key = key.replace('-','_')
        self.data[key] = value

    def __getitem__(self, key):
        key = str(key).lower()
        if self.request is True:
            key = key.replace('-','_')
        if key in self.data:
            return self.get(key)
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        try:
            key = str(key).lower()
            if self.request is True:
                key = key.replace('-','_')
            del self.data[key]
        except KeyError:
            pass

    def __contains__(self, key):
        key = str(key).lower()
        if self.request is True:
            key = key.replace('-','_')
        return key in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def update(self, headers):
        self.data.update(headers)

    def get(self, key, default=None):
        try:
            key = str(key).lower()
            if self.request is True:
                key = key.replace('-','_')
            if is_byte_string(self.data[key]):
                return self.data[key]
            else:
                return str(self.data[key]).encode('utf-8')
        except KeyError:
            return default
