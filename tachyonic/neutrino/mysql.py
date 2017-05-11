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

import sys
import logging
if sys.version[0] == '2':
    import thread
    from Queue import Queue
else:
    import _thread as thread
    from queue import Queue
import datetime

import pymysql as MySQLdb
import pymysql.cursors as cursors
import tachyonic as root
from tachyonic.neutrino.shrek import Shrek
from tachyonic.common.timer import timer as nfw_timer
from tachyonic.common.strings import filter_none_text
from tachyonic.common.threaddict import ThreadDict
from tachyonic.common.dt import utc_time


log = logging.getLogger(__name__)


if hasattr(root, 'debug'):
    debug = root.debug
else:
    debug = True


class MysqlWrapper(object):
    def __init__(self, name='default', host=None, username=None,
                 password=None, database=None, debug=debug):
        self.name = name
        self.debug = debug

        self.db = connect(host=host,
                          username=username, password=password,
                          database=database)
        self.cursor = self.db.cursor(cursors.DictCursor)

        self.uncommited = False

    def ping(self):
        self.db.ping(True)

    def close(self):
        try:
            if self.uncommited is True:
                self.rollback()
                # Autocommit neccessary for next request to start new transactions.
                # If not applied select queries will return cached results
                self.commit()
        except MySQLdb.OperationalError as e:
            log.error(e)

    def last_row_id(self):
        return self.cursor.lastrowid

    def last_row_count(self):
        return self.cursor.rowcount

    def execute(self, query=None, params=None):
        result = execute(self.cursor, query, params)
        self.uncommited = True
        return result

    def fields(self, table):
        fields = {}
        result = self.execute("DESCRIBE %s" % (table,))
        for f in result:
            name = f['Field']
            fields[name] = f
        return fields

    def lock(self, table, write=True):
        if write is True:
            lock = "WRITE"
        else:
            lock = "READ"
        query = "LOCK TABLES %s %s" % (table, lock)
        result = execute(self.cursor, query)
        return result

    def unlock(self):
        query = "UNLOCK TABLES"
        result = execute(self.cursor, query)
        return result

    def commit(self):
        if self.uncommited is True:
            commit(self.db)
            self.uncommited = False

    def rollback(self):
        if self.uncommited is True:
            rollback(self.db)


shrek = Shrek('mysql', MysqlWrapper)


def Mysql(name='default', host=None, username=None,
          password=None, database=None, debug=debug):

    db = shrek.get(name, host=host,
                   username=username, password=password,
                   database=database)
    db.ping()
    return db


def connect(host, username, password, database):
    if debug is True:
        timer = nfw_timer()
        log.debug("Connecting Database Connection" +
                  " (server=%s,username=%s,database=%s)" %
                  (host, username,
                   database))

    conn = MySQLdb.connect(host=host,
                           user=username,
                           passwd=password,
                           db=database,
                           use_unicode=True,
                           charset='utf8',
                           autocommit=False)
    if debug is True:
        timer = nfw_timer(timer)
        log.debug("Connected Database Connection" +
                  " (server=%s,username=%s,database=%s,%s,%s,%s)" %
                  (host,
                   username,
                   database,
                   conn.get_server_info(),
                   conn.get_host_info(),
                   conn.thread_id) +
                  " (DURATION: %s)" % (timer))
    return conn


def _log_query(query=None, params=None):
    parsed = []
    if params is not None:
        for param in params:
            if isinstance(param, int) or isinstance(param, float):
                parsed.append(param)
            else:
                parsed.append('\'' + filter_none_text(param) + '\'')
    try:
        log_query = query % tuple(parsed)
    except Exception:
        log_query = query

    return log_query


def _parsed_params(params):
    parsed = []
    if params is not None:
        for param in params:
            if isinstance(param, bool):
                if param is True:
                    parsed.append(1)
                else:
                    parsed.append(0)
            else:
                parsed.append(param)
    return parsed

def _parsed_results(results):
    for result in results:
        for field in result:
            if isinstance(result[field], datetime.datetime):
                result[field] = utc_time(result[field])
    return results


def execute(cursor, query=None, params=None):
    if debug is True:
        timer = nfw_timer()

    log_query = _log_query(query, params)
    parsed = _parsed_params(params)

    try:
        cursor.execute(query, parsed)
    except MySQLdb.IntegrityError as e:
        code, value = e
        log.error("Query %s" % (log_query))
        raise MySQLdb.IntegrityError(code, value)

    result = cursor.fetchall()

    if debug is True:
        timer = nfw_timer(timer)
        if timer > 0.1:
            log.debug("!SLOW! Query %s (DURATION: %s)" % (log_query, timer))
        else:
            log.debug("Query %s (DURATION: %s)" % (log_query, timer))

    return _parsed_results(result)


def commit(db):
    if debug is True:
        timer = nfw_timer()

    db.commit()

    if debug is True:
        timer = nfw_timer(timer)
        if timer > 0.1:
            log.debug("!SLOW! Commit" +
                      " (%s,%s,%s) (DURATION: %s)" %
                      (db.get_server_info(),
                       db.get_host_info(),
                       db.thread_id,
                       timer))
        else:
            log.debug("Commit" +
                      "(%s,%s,%s) (DURATION: %s)" %
                      (db.get_server_info(),
                       db.get_host_info(),
                       db.thread_id,
                       timer))


def rollback(db):
    if debug is True:
        timer = nfw_timer()

    db.rollback()

    if debug is True:
        timer = nfw_timer(timer)
        if timer > 0.1:
            log.debug("!SLOW! Rollback" +
                      " (%s,%s,%s) (DURATION: %s)" %
                      (db.get_server_info(),
                       db.get_host_info(),
                       db.thread_id,
                       timer))
        else:
            log.debug("Rollback" +
                      " (%s,%s,%s) (DURATION: %s)" %
                      (db.get_server_info(),
                       db.get_host_info(),
                       db.thread_id,
                       timer))
