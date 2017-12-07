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

import sys
import logging
import _thread as thread
from queue import Queue
import datetime

import pymysql as MySQLdb
import pymysql.cursors as cursors
from pymysql.constants import COMMAND

from tachyonic.neutrino.shrek import Shrek
from tachyonic.neutrino.timer import timer
from tachyonic.neutrino.strings import filter_none_text
from tachyonic.neutrino.threaddict import ThreadDict
from tachyonic.neutrino.dt import utc_time

log = logging.getLogger(__name__)

def _log(db, msg, elapsed=0):
    """Debug Log Function

    Function to log in the case where debugging
    is enabled.

    Args:
        db (object): pymysql connection object.
        msg (str): Log message.
        elapsed (float): Time elapsed.
    """
    if log.getEffectiveLevel() <= logging.DEBUG:
        log_msg = (msg +
                   " (DURATION: %.4fs) (%s,%s,%s)" %
                   (elapsed,
                    db.get_server_info(),
                    db.get_host_info(),
                    db.thread_id,
                    ))
        if elapsed > 0.1:
            log_msg = "!SLOW! " + log_msg
        log.debug(log_msg)

class MysqlWrapper(object):
    """Simple Mysql Interface.

    Ensure datatime is GMT/UTC as per Tachyonic standard and provides
    logging and simple to use interface for interacting with MariaDb/Mysql.

    Args:
        name (str): Unique redis thread for specific pool/session.
        host (str): Host or IP of MySQL/Maraidb Server.
        username (str): Database username.
        password (str): Database password.
        database (str): Database for connection.
    """
    def __init__(self, name='default', host=None, username=None,
                 password=None, database=None):
        self.name = name
        self.utc_tz = False

        self.db = _connect(host=host,
                           username=username, password=password,
                           database=database)
        self.cursor = self.db.cursor(cursors.DictCursor)

        self.uncommited = False
        self.locks = False

    def ping(self):
        """Check if the server is alive.

        Auto-Reconnect if not, and return false when reconnecting.
        """
        return _ping(self.db)

    def close(self):
        """Close Server Session.

        Send the quit message, close the socket and rollback any
        uncommited changes.
        """
        try:
            if self.locks is True:
                self.unlock()
            if self.uncommited is True:
                self.rollback()
                # Autocommit neccessary for next request to start new transactions.
                # If not applied select queries will return cached results
                self.commit()
        except MySQLdb.OperationalError as e:
            log.error(e)

    def last_row_id(self):
        """Return last row id.

        This method returns the value generated for an AUTO_INCREMENT
        column by the previous INSERT or UPDATE statement or None
        is no column available or rather AUTO_INCREMENT not used.
        """
        return self.cursor.lastrowid

    def last_row_count(self):
        """Return last row count.

        This method returns the number of rows returned for SELECT statements,
        or the number of rows affected by DML statements such as INSERT
        or UPDATE.
        """

        return self.cursor.rowcount

    def execute(self, query=None, params=None):
        """Execute SQL Query.

        Args:
            query (str): SQL Query String.
            params (list): Query values as per query string.

        Returns:
            Parsed Results list containing dictionaries with field values per row.
        """
        if isinstance(params, str):
            # If only one paramter string value, formated to list
            params = [ params ]
        elif isinstance(params, tuple):
            # Convert params to list if tuple.
            params = list(params)

        result = _execute(self.db, self.cursor, query, params)
        self.uncommited = True

        return result

    def fields(self, table):
        """Return table columns.

        Args:
            table (str): Database table.

        Returns a list of columns on specified sql table.
        """
        fields = {}
        result = self.execute("DESCRIBE %s" % (table,))
        for f in result:
            name = f['Field']
            fields[name] = f
        return fields

    def lock(self, table, write=True):
        """Lock specified table.

        MySQL enables client sessions to acquire table locks explicitly for the
        purpose of cooperating with other sessions for access to tables, or to
        prevent other sessions from modifying tables during periods when a
        session requires exclusive access to them. A session can acquire or
        release locks only for itself. One session cannot acquire locks for
        another session or release locks held by another session.

        LOCK TABLES implicitly releases any table locks held by the current
        session before acquiring new locks.

        Args:
            table (str): Database table.
            lock (bool):
                * False: The session that holds the lock can read the table
                    (but not write it). Multiple sessions can acquire a READ
                    for the table at the same time. Other sessions can read the
                    the table without explicitly acquiring a READ lock.
                * True: The session that holds the lock can read and write the
                    table. Only the session that holds the lock can access the
                    table. No other session can access it until the lock is
                    released. Lock requests for the table by other sessions
                    block while the WRITE lock is held.
        """
        if write is True:
            lock = "WRITE"
        else:
            lock = "READ"
        query = "LOCK TABLES %s %s" % (table, lock)
        _execute(self.cursor, query)
        self.locks = True

    def unlock(self):
        """Unlock tables.

        UNLOCK TABLES explicitly releases any table locks held by the current
        session.
        """
        query = "UNLOCK TABLES"
        _execute(self.cursor, query)
        self.locks = False

    def commit(self):
        """Commit Transactionl Queries.

        If the database and the tables support transactions, this commits the
        current transaction; otherwise this method successfully does nothing.
        """
        if self.uncommited is True:
            _commit(self.db)
            self.uncommited = False

    def rollback(self):
        """Rollback Transactional Queries

        If the database and tables support transactions, this rolls back
        (cancels) the current transaction; otherwise a NotSupportedError is raised.
        """
        if self.uncommited is True:
            _rollback(self.db)


# Create pooling group for MysqlWrapper using Shrek
shrek = Shrek(MysqlWrapper)

def Mysql(name='default', host=None, username=None,
          password=None, database=None):
    """Connection objects are returned by the connect() function.

    Uses Neutrino Shrek for pooling mysql sessions on per thread basis.

    Args:
        name (str): Unique mysql thread for specific pool/session.
        host (str): Host or IP of MySQL/Maraidb Server.
        username (str): Database username.
        password (str): Database password.
        database (str): Database for connection.

    Returns connection object.
    """
    mysql_wrapper = shrek.get(name, host=host,
                              username=username, password=password,
                              database=database)

    # PING AND RECONNECT
    ping = mysql_wrapper.ping()

    # SET TO UTC TIMEZONE
    # specifically to SQL query based functions such as now()
    if ping is False or mysql_wrapper.utc_tz is False:
        mysql_wrapper.execute('SET time_zone = %s', '+00:00')
        mysql_wrapper.utc_tz = True

    return mysql_wrapper

def _connect(host, username, password, database):
    """Connection objects are returned by the connect() function.

    Generally you do not need to use this function directly, as an
    instance is created by default when the Mysql class is initialized.

    Args:
        host (str): Host or IP of MySQL/Maraidb Server.
        username (str): Database username.
        password (str): Database password.
        database (str): Database for connection.

    Returns connection object.
    """
    with timer() as elapsed:
        if log.getEffectiveLevel() <= logging.DEBUG:
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
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.debug("Connected Database Connection" +
                      " (server=%s,username=%s,database=%s,%s,%s,%s)" %
                      (host,
                       username,
                       database,
                       conn.get_server_info(),
                       conn.get_host_info(),
                       conn.thread_id) +
                      " (DURATION: %s)" % (elapsed()))
        return conn


def _log_query(query=None, params=None):
    """Parse query to log.

    Returns SQL Query (string)
    """
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
    """Parse SQL paramters provided to query.

    Returns list of values.
    """
    parsed = []
    if params is not None:
        for param in params:
            if isinstance(param, bool):
                # Modify python bool to 0/1 integer.
                # Mysql has no bool field.
                if param is True:
                    parsed.append(1)
                else:
                    parsed.append(0)
            # MYSQL cannot store timezone information in datetime field.
            # Its therefor recommended to use the:
            #    tachyonic.neutrino.dt.datetime() singleton.
            # christiaan.rademan@gmail.com
            #elif isinstance(param, datetime.datatime):
                # Store as UTC_TIME if datetime
            #    parsed.append(str(utc_time(param)))
            else:
                parsed.append(param)
    return parsed

def _parsed_results(results):
    """Parse results returned by SQL Query.

    Returns list of rows.
    """
    # Since the database connection timezone is set to +00:00
    # all functions such as now() etc will store in UTC/GMT time.
    # For datatime objects sent as params it will be converted to UTC
    # Its therefor not neccessary to parse datatime. However this code
    # is here for any other results that may require paring in future.
    # christiaan.rademan@gmail.com.
    #for result in results:
    #    for field in result:
    #        if isinstance(result[field], datetime.datetime):
    #            # Format Date time to UTC Time.
    #            result[field] = utc_time(result[field])
    return results

def _execute(db, cursor, query=None, params=None):
    """Execute SQL Query.

    Generally you do not need to use this function directly, as its
    provided as method of the MysqlWrapper class.

    Too perform a query, you first need a cursor, and then you can execute
    queries on it.

    Args:
        db: (object): pymysql connection object
        cursor (object): pymysql cursor provided by connection.
        query (str): SQL Query String.
        params (list): Query values as per query string.

    Returns:
        Parsed Results list containing dictionaries with field values per row.
    """
    with timer() as elapsed:
        log_query = _log_query(query, params)
        parsed = _parsed_params(params)

        try:
            cursor.execute(query, parsed)
        except MySQLdb.IntegrityError as e:
            code, value = e
            log.error("Query %s" % (log_query))
            raise MySQLdb.IntegrityError(code, value)

        result = cursor.fetchall()
        _log(db, "Query %s" % log_query, elapsed())

        return _parsed_results(result)

def _commit(db):
    """Commit Transactionl Queries.

    Generally you do not need to use this function directly, as its
    provided as method of the MysqlWrapper class.

    If the database and the tables support transactions, this commits the
    current transaction; otherwise this method successfully does nothing.

    Args:
        db (object): pymysql connection object.
        debug (bool): Wether to log debug output.
    """
    with timer() as elapsed:
        db.commit()
        _log(db, "Commit", elapsed())

def _rollback(db):
    """Rollback Transactional Queries

    Generally you do not need to use this function directly, as its
    provided as method of the MysqlWrapper class.

    If the database and tables support transactions, this rolls back
    (cancels) the current transaction; otherwise a NotSupportedError is raised.

    Args:
        db (object): pymysql connection object.
    """
    with timer() as elapsed:
        db.rollback()
        _log(db, "Rollback", elapsed())

def _ping(db):
        """Check if the server is alive.

        Auto-Reconnect if not, and return false when reconnecting.
        """
        if db._sock is None:
            db.connect()
            return False
        else:
            try:
                db._execute_command(COMMAND.COM_PING, "")
                db._read_ok_packet()
                return True
            except Exception:
                db.connect()
                return False
