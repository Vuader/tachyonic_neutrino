from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging
if sys.version[0] == '2':
    import thread
    from Queue import Queue
else:
    import _thread as thread
    from queue import Queue

import pymysql as MySQLdb
import pymysql.cursors as cursors

from tachyonic.neutrino.utils.general import timer as nfw_timer

log = logging.getLogger(__name__)


class Mysql(object):
    _pool = {}
    _credentials = {}
    _thread = {}

    def __init__(self, name=None, host=None, username=None,
                 password=None, database=None):

        self.thread_id = thread.get_ident()

        if name is not None:
            self.name = name
        else:
            self.name = 'default'

        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.initialize()

    def initialize(self):
        if self.name not in self._pool:
            self._pool[self.name] = Queue(maxsize=0)

        if self.name not in self._credentials:
            self._credentials[self.name] = {}
        if self.host is not None:
            self._credentials[self.name]['host'] = self.host
        if self.username is not None:
            self._credentials[self.name]['username'] = self.username
        if self.password is not None:
            self._credentials[self.name]['password'] = self.password
        if self.database is not None:
            self._credentials[self.name]['database'] = self.database

        self.host = self._credentials[self.name].get('host', '127.0.0.1')
        self.username = self._credentials[self.name].get('username', '')
        self.password = self._credentials[self.name].get('password', '')
        self.database = self._credentials[self.name].get('database', '')

        if (self.thread_id in self._thread and
                self.name in self._thread[self.thread_id]):
            pass
        else:
            if self.thread_id not in self._thread:
                self._thread[self.thread_id] = {}
            if self._pool[self.name].empty():
                conn = connect(self.host,
                               self.username,
                               self.password,
                               self.database)
                conn.ping(True)
                cursor = conn.cursor(cursors.DictCursor)
            else:
                conn = self._pool[self.name].get(True)

                conn.ping(True)
                cursor = conn.cursor(cursors.DictCursor)
            self._thread[self.thread_id][self.name] = {}
            self._thread[self.thread_id][self.name]['db'] = conn
            self._thread[self.thread_id][self.name]['cursor'] = cursor
            self._thread[self.thread_id][self.name]['uncommited'] = False

    @staticmethod
    def close_all():
        thread_id = thread.get_ident()
        if thread_id in Mysql._thread:
            for o in Mysql._thread[thread_id]:
                db = Mysql._thread[thread_id][o]['db']
                uncommited = Mysql._thread[thread_id][o]['uncommited']
                if uncommited is True:
                    rollback(db)
                    # Autocommit neccessary for next request to start new transactions.
                    # If not applied select queries will return cached results
                    commit(db)
                Mysql._pool[o].put_nowait(db)
            del Mysql._thread[thread_id]

    def close(self):
        try:
            if (self.thread_id in self._thread and
                    self.name in self._thread[self.thread_id]):
                db = self._thread[self.thread_id][self.name]['db']
                uncommited = self._thread[self.thread_id][self.name]['uncommited']
                if uncommited is True:
                    rollback(db)
                self._pool[self.name].put_nowait(db)
                del self._thread[self.thread_id][self.name]
        except MySQLdb.OperationalError as e:
            del self._thread[self.thread_id][self.name]
            log.error("mysql error" % (e))

    def last_row_id(self):
        try:
            cursor = self._thread[self.thread_id][self.name]['cursor']
            return cursor.lastrowid
        except MySQLdb.OperationalError as e:
            log.error("mysql error, attempt to re-initialize (%s)" % (e))
            del self._thread[self.thread_id][self.name]
            self.initialize()
            return None

    def last_row_count(self):
        try:
            cursor = self._thread[self.thread_id][self.name]['cursor']
            return cursor.rowcount
        except MySQLdb.OperationalError as e:
            log.error("mysql error, attempt to re-initialize (%s)" % (e))
            del self._thread[self.thread_id][self.name]
            self.initialize()
            return None

    def _ping(self):
        try:
            cursor = self._thread[self.thread_id][self.name]['cursor']
            execute(cursor, "SELECT VERSION()")
            return True
        except:
            return False

    def execute(self, query=None, params=None):
        try:
            cursor = self._thread[self.thread_id][self.name]['cursor']
            result = execute(cursor, query, params)
            self._thread[self.thread_id][self.name]['uncommited'] = True
            return result
        except MySQLdb.OperationalError as e:
            if self._ping is False:
                log.error("mysql error, attempt to re-initialize (%s)" % (e))
                del self._thread[self.thread_id][self.name]
                self.initialize()
                return execute(self, query, params)
            else:
                raise MySQLdb.OperationalError(e)

    def fields(self, table):
        fields = {}
        result = self.execute("DESCRIBE %s" % (table,))
        for f in result:
            name = f['Field']
            fields[name] = f
        return fields

    def lock(self, table, write=True):
        try:
            if write is True:
                lock = "WRITE"
            else:
                lock = "READ"
            cursor = self._thread[self.thread_id][self.name]['cursor']
            query = "LOCK TABLES %s %s" % (table, lock)
            result = execute(cursor, query)
            return result
        except MySQLdb.OperationalError as e:
            if self._ping is False:
                log.error("mysql error, attempt to re-initialize (%s)" % (e))
                del self._thread[self.thread_id][self.name]
                self.initialize()
                return lock(self, table, write)
            else:
                raise MySQLdb.OperationalError(e)

    def unlock(self):
        try:
            cursor = self._thread[self.thread_id][self.name]['cursor']
            query = "UNLOCK TABLES"
            result = execute(cursor, query)
            return result
        except MySQLdb.OperationalError as e:
            if self._ping is False:
                log.error("mysql error, attempt to re-initialize (%s)" % (e))
                del self._thread[self.thread_id][self.name]
                self.initialize()
                return self.unlock()
            else:
                raise MySQLdb.OperationalError(e)

    def commit(self):
        try:
            db = self._thread[self.thread_id][self.name]['db']
            if self._thread[self.thread_id][self.name]['uncommited'] is True:
                commit(db)
                self._thread[self.thread_id][self.name]['uncommited'] = False
        except MySQLdb.OperationalError as e:
            log.error("mysql error, attempt to re-initialize (%s)" % (e))
            del self._thread[self.thread_id][self.name]
            self.initialize()
            self.commit()

    def rollback(self):
        try:
            db = self._thread[self.thread_id][self.name]['db']
            rollback(db)
            commit(db)
            self._thread[self.thread_id][self.name]['uncommited'] = False
        except MySQLdb.OperationalError as e:
            log.error("mysql error, attempt to re-initialize (%s)" % (e))
            del self._thread[self.thread_id][self.name]
            self.initialize()
            self.rollback()


def _log_query(query=None, params=None):
    try:
        if isinstance(params, tuple):
            log_query = query % params
        elif isinstance(params, list):
            log_query = query % tuple(params)
        else:
            log_query = query
    except Exception:
        log_query = query

    return log_query


def connect(host, username, password, database):
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


def execute(cursor, query=None, params=None):
    timer = nfw_timer()

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

    log_query = _log_query(query, parsed)

    try:
        cursor.execute(query, parsed)
    except MySQLdb.IntegrityError as e:
        code, value = e
        log.error("SQL Query %s" % (log_query))
        raise MySQLdb.IntegrityError(code, value)

    result = cursor.fetchall()

    timer = nfw_timer(timer)
    if timer > 0.1:
        log.debug("SQL !SLOW! Query %s (DURATION: %s)" % (log_query, timer))
    else:
        log.debug("SQL Query %s (DURATION: %s)" % (log_query, timer))

    return result


def commit(db):
    timer = nfw_timer()
    db.commit()
    timer = nfw_timer(timer)
    if timer > 0.1:
        log.debug("SQL !SLOW! Commit" +
                  " (%s,%s,%s) (DURATION: %s)" %
                  (db.get_server_info(),
                   db.get_host_info(),
                   db.thread_id,
                   timer))
    else:
        log.debug("SQL Commit" +
                  "(%s,%s,%s) (DURATION: %s)" %
                  (db.get_server_info(),
                   db.get_host_info(),
                   db.thread_id,
                   timer))


def rollback(db):
    timer = nfw_timer()
    db.rollback()
    timer = nfw_timer(timer)
    if timer > 0.1:
        log.debug("SQL !SLOW! Rollback" +
                  " (%s,%s,%s) (DURATION: %s)" %
                  (db.get_server_info(),
                   db.get_host_info(),
                   db.thread_id,
                   timer))
    else:
        log.debug("SQL Rollback" +
                  " (%s,%s,%s) (DURATION: %s)" %
                  (db.get_server_info(),
                   db.get_host_info(),
                   db.thread_id,
                   timer))


class Testing():
    def __init__(self, queries):
        self.queries = queries
        self.execute_count = 0
        self._last_row_id = None
        self._last_row_count = None

    def last_row_id(self):
        return self._last_row_id

    def last_row_count(self):
        return self._last_row_count

    def _query(self):
        if len(self.queries) > self.execute_count:
            q = self.queries[self.execute_count]
            if isinstance(q, dict):
                self.execute_count = self.execute_count + 1
                return q
            else:
                raise Exception("Expected dictionary")
        else:
            return {}

    def commit(self):
        if len(self.queries) != self.execute_count:
            raise Exception("Not all test sql queries executed")

    def rollback(self):
        pass

    def execute(self, query, values=None):
        q = self._query()
        if query != q.get('query'):
            raise Exception("Query not matched %s == %s" % (query, q.get('query')))
        if q.get('values') is not None:
            if values is not None:
                if (isinstance(q.get('values'), list) or
                        isinstance(q.get('values'), tuple) and
                        (isinstance(values, list) or
                            isinstance(values, tuple))):
                    if len(values) == len(q.get('values')):
                        for (i, v) in enumerate(q.get('values')):
                            if values[i] != v:
                                raise Exception("Values not matched %s == %s" % (values[i],v))
                        self._last_row_count = q.get('last_row_count')
                        self._last_row_id = q.get('last_row_id')
                    else:
                        raise Exception("Values not matched")
                else:
                    raise Exception("Values not matched")
            else:
                raise Exception("Values not matched")

        return q.get('result', [])
