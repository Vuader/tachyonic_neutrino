# -*- coding: utf-8 -*-
# Copyright (c) 2017, Christiaan Frans Rademan.
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

import sys
import logging

from tachyonic.neutrino import exceptions

log = logging.getLogger(__name__)


def import_module(module):
    log.debug('Importing module: %s' % module)
    __import__(module)
    log.debug('Importing module: %s (Completed)' % module)
    return sys.modules[module]

def import_modules(modules):
    loaded = {}
    for module in modules:
        m = import_module(module)
        loaded[module] = m

    return loaded

def get_class(cls):
    if cls is None:
        raise ImportError("Cannot import 'None'")
    try:
        cs = cls.split('.')
        l = len(cs)
        d = cs[l-1]
        m = ".".join(cs[0:l-1])
        module = import_module(m)
    except:
        raise ImportError("Cannot import '%s'" % cls)

    if hasattr(module, d):
        return getattr(module, d)
    else:
        raise ImportError("Cannot import '%s'" % cls)

def init_classes(classes):
    loaded = []

    for cls in classes:
        loaded.append(get_class(cls)())

    return loaded
