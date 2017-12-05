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

def parse_datetime(datetime_obj):
    """Parse Datetime Object.

    * Validates if valid datetime object.
    * Used to set timezone to UTC if naive.

    Returns datetime object with UTC timezone.
    """
    if isinstance(datetime_obj, datetime.datetime):
        if datetime_obj.tzname() is None:
            datetime_obj = pytz.utc.localize(datetime_obj)

        return datetime_obj
    else:
        raise TypeError('parse_datetime: Not datetime object')


def utc_time(datetime_obj=None, source_tz=None):
    """Return UTC DataTime.

    Return UTC timezone from specified source timezone.

    Args:
        datetime_obj (datatime.datatime): DataTime Object (defaults to now)
        source_tz (str): Source Timezone (defaults to host)

    Returns datetime.datetime object.
    """
    if datetime_obj is None:
        datetime_obj = datetime.datetime.now()

    if source_tz is None:
        source_tz = str(get_localzone())

    datetime_obj = pytz.timezone(source_tz).localize(datetime_obj)
    utc = pytz.timezone('UTC')

    return datetime_obj.astimezone(utc)

def from_utc(utc_time, destination_tz=None):
    """Return Destination DataTime from UTC.

    Args:
        utc_time (datetime.datetime): Datetime Object
        destination_tz (str): Destination Timezone (defaults to host)

    Returns datetime.datetime object.
    """
    if destination_tz is None:
        tz = get_localzone()
    else:
        tz = pytz.timezone(destination_tz)

    return utc_time.astimezone(tz)

def timezones():
    """Return list all timezones.
    """
    return pytz.all_timezones


class Datetime(object):
    """ Provide simple Datetime Interface.

    UTC is the time standard commonly used across the world. The world's timing
    centers have agreed to keep their time scales closely synchronized - or
    coordinated - therefore the name Coordinated Universal Time.

    All HTTP date/time stamps MUST be represented in Greenwich Mean Time (GMT),
    without exception. For the purposes of HTTP, GMT is exactly equal to UTC
    (Coordinated Universal Time). This is indicated in the first two formats by
    the inclusion of "GMT" as the three-letter abbreviation for time zone, and
    MUST be assumed when reading the asctime format. HTTP-date is case sensitive
    and MUST NOT include additional LWS beyond that specifically included as SP
    in the grammer.

    Its good practice to use only one timezone within an application. Using
    different timezones and standards can result in confusion.

    Tachyonic, mysql api interface will set timezone to +00:00 GMT/UTC for
    sql server functions to store current time such as now().

    However when the time is returned from using mysql api in a result it will
    be converted to UTC time function.

    IMPORTANT: Mysql / Mariadb do not store timezone related information
        in datetime fields.

    Attributes:
        now (datetime.datetime): Current local time in UTC. (readonly)
        local (datetime.datetime). Current local time in local zone. (readonly)
        tz (str): Local Timezone. (read & write)
        timezones (list): List of timezones for tz attribute. (readonly)
    """
    def __new__(cls):
        # Please keep singleton for global TZ. (christiaan.rademan@gmail.com)
        if not hasattr(cls, '_instance'):
            cls._instance = super(Datetime, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_init'):
            self.tz = get_localzone()
            self._init = True

    def __getattr__(self, name):
        if name == 'now':
            return utc_time(source_tz=self.tz)
        elif name == "local":
            return from_utc(utc_time(), self.tz)
        elif name == "timezones":
            return timezones()
        else:
            raise AttributeError("Unknown attribute %s" % name)

    def __setattr__(self, name, value):
        if name == 'tz':
            if str(value) in timezones():
                super(Datetime, self).__setattr__('tz', str(value))
            else:
                raise AttributeError("Unknown Timezone %s" % value)
        elif name == "_init":
                super(Datetime, self).__setattr__('_init', True)
        else:
            raise AttributeError("Unknown Attribute %s on tachyoniuc.dt.datetime"
                                 % name)

    def from_utc(self, destination_tz=None):
        """Return Current UTC in destination timezone.

        Args:
            destination_tz (str): Destination Timezone (defaults to host)

        Returns datetime.datetime object.
        """
        if destination_tz is None:
            destination_tz = self.tz
        return from_utc(self.now, destination_tz)

    def http(self):
        """Formatted Date for HTTP

        Greenwich Mean Time. HTTP dates are always expressed in GMT, never in
        local time. UTC is equal to GMT (+00:00)
        """
        return str(datetime.datetime.strftime(self.now, "%a, %d %b %Y" +
                                              " %H:%M:%S" +
                                              " GMT"))


    def _format(self, datetime=None, destination_tz=None):
        if datetime is None:
            datetime = self.from_utc(destination_tz)
        else:
            datetime = parse_datetime(datetime)
            datetime = from_utc(datetime, self.tz)

        return datetime

    def f_date(self, datetime=None, destination_tz=None):
        """Formatted Date.

        Many countries have adopted the ISO standard of year-month-day. For
            example, 2015-3-30 (SAST).

        Appends short timezone name.

        Args:
            datetime (datetime): Datetime object. (Optional)
            destination_tz (str): Destination Timezone.
                List of valid entries in timezones attribute.

        Returns string formatted date.
        """
        datetime = self._format(datetime, destination_tz)

        return(datetime.strftime('%Y-%m-%d ') + "(" +
               datetime.tzname() + ")")

    def f_time(self, datetime=None, destination_tz=None):
        """Formatted Time.

        Many countries have adopted the ISO standard of year-month-day. For
            example, 2015-3-30 (SAST).

        Appends short timezone name.

        Args:
            datetime (datetime): Datetime object. (Optional)
            destination_tz (str): Destination Timezone.
                List of valid entries in timezones attribute.

        Returns string formatted date.
        """
        datetime = self._format(datetime, destination_tz)

        return(datetime.strftime('%H:%M:%S ') + "(" +
               datetime.tzname() + ")")

    def f_datetime(self, datetime=None, destination_tz=None):
        """Formatted Date & Time.

        Many countries have adopted the ISO standard of year-month-day
        hour:minute:seconds. For
            example, 2015-3-30 10:15:25 (SAST).

        Appends short timezone name.

        Args:
            datetime (datetime): Datetime object. (Optional)
            destination_tz (str): Destination Timezone.
                List of valid entries in timezones attribute.

        Returns string formatted date.
        """
        datetime = self._format(datetime, destination_tz)

        return(datetime.strftime('%Y-%m-%d %H:%M:%S ') + "(" +
               datetime.tzname() + ")")

    def isodate(self, datetime=None, destination_tz=None):
        """ ISO Formatted Date.

        Return a string representing the date in ISO 8601 format, ‘YYYY-MM-DD’

        Args:
            datetime (datetime): Datetime object. (Optional)
            destination_tz (str): Destination Timezone.
                List of valid entries in timezones attribute.

        Returns string formatted date.
        """
        datetime = self._format(datetime, destination_tz)

        return datetime.strftime('%Y-%m-%d')

    def diff(self, datetime, datetime2=None):
        """Return difference between two datetimes.

        Equation: datetime2 - datetime

        Args:
            datetime (datetime): Datetime to compare.
            datetime2 (datetime): Datetime to compare. (default current)

        Returns difference in seconds (float)
        """
        if datetime2 is None:
            datetime2 = self.now

        if datetime.tzname() != datetime2.tzname():
            raise TypeError('cannot compare datetime with different timezones.')

        datetime = parse_datetime(datetime)

        return(datetime2 - datetime).total_seconds()

    def __str__(self):
        return str(self.f_datetime())
