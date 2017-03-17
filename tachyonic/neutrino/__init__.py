# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .wsgi import app
from . import metadata
"""
from . import config
from . import model
from . import mysql
from . import password
from . import restart
from . import restclient
from . import template
from . import utils
from . import web

from .config import Config
from .constants import *
from .exceptions import *
from .headers import Headers
from .logger import Logger
from .model import Model
from .model import ModelDict
from .mysql import Mysql
from .policy import Policy
from .redissy import redis
from .request import Request
from .response import Response
from .response import http_moved_permanently
from .response import http_found
from .response import http_see_other
from .response import http_temporary_redirect
from .response import http_permanent_redirect
from .restclient import RestClient
from .router import Router
from .router import view
from .session import SessionRedis
from .session import SessionFile
from .utils import random_id, timer, ThreadDict
from .web import bootstrap3
"""

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

_cc = 0

def creation_counter():
    global _cc
    _cc += 1
    return _cc

