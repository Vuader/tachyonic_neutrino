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

import datetime
import logging

import pytz
from tzlocal import get_localzone

log = logging.getLogger(__name__)


def utc_time(py_datetime_obj=None, source_tz=None):
    if py_datetime_obj is None:
        local_system_utc = datetime.datetime.utcnow()
        return pytz.utc.localize(local_system_utc)
    else:
        if source_tz is None:
            source_tz = str(get_localzone())

        py_datetime_obj = pytz.timezone(source_tz).localize(py_datetime_obj)
        utc = pytz.timezone('UTC')
        return py_datetime_obj.astimezone(utc)


def from_utc(utc_time, destination=None):
    if destination is None:
        tz = get_localzone()
    else:
        tz = pytz.timezone(destination)

    return utc_time.astimezone(tz)


def timezones():
    return pytz.all_timezones


class Datetime(object):
    def __init__(self):
        self.tz = None

    def __getattr__(self, name):
        if name == 'now':
            return utc_time()
        elif name == "local":
            return from_utc(utc_time(), self.tz)
        elif name == "timezones":
            return timezones()
        else:
            raise AttributeError("Unknown attribute %s" % name)

    def __setattr__(self, name, value):
        if name == 'tz':
            if value is None:
                super(Datetime, self).__setattr__('tz', None)
            elif value in timezones():
                super(Datetime, self).__setattr__('tz', value)
            else:
                raise AttributeError("Unknown Timezone %s" % value)
