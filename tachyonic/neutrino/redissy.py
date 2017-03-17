from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import redis as rd

log = logging.getLogger(__name__)


def redis(config):
    redis_config = config.get('redis')
    host = redis_config.get('server', 'localhost')
    port = redis_config.get('port', 6379)
    db = redis_config.get('db', 0)

    return rd.StrictRedis(host=host, port=port, db=db)
